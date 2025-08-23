# lottery_data_mcp.py — OMEGA MCP Lottery Data Ingestion (Enterprise-Grade)
# -*- coding: utf-8 -*-
"""
Ingesta robusta de datos de lotería (CSV/JSON/API) con validación básica,
particionado por fecha, compresión y metadatos para trazabilidad.
Uso:
    from lottery_data_mcp import ProductionLotteryDataMCP, SourceConfig
    mcp = ProductionLotteryDataMCP(data_dir="data/lottery_ingestion")
    mcp.ingest([SourceConfig(kind="csv", name="kabala_hist", url="https://.../kabala.csv")])
"""
from __future__ import annotations
import os
import re
import io
import gc
import csv
import json
import gzip
import time
import math
import base64
import hashlib
import logging
import datetime as dt
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Iterable

import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

# ---------------------------- Logging ---------------------------------

def setup_logger(name: str = "omega.mcp.lottery", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger

logger = setup_logger()

# ---------------------------- Config ----------------------------------

@dataclass
class SourceConfig:
    kind: str                     # "csv" | "json" | "api"
    name: str
    url: Optional[str] = None
    local_path: Optional[str] = None
    delimiter: str = ","          # para CSV
    encoding: str = "utf-8"
    date_col: Optional[str] = None
    validate_numbers: bool = True
    lower: int = 1                # rango de bolillas
    upper: int = 40
    timeout_seconds: int = 20


@dataclass
class ProductionLotteryDataMCP:
    data_dir: str = "data/lottery_ingestion"
    write_parquet: bool = False  # fallback a CSV.GZ si no hay pyarrow
    partition_by_day: bool = True
    keep_raw: bool = True        # guardar también el crudo
    _os_makedirs_done: bool = field(default=False, init=False)

    def __post_init__(self):
        os.makedirs(self.data_dir, exist_ok=True)
        self._os_makedirs_done = True
        logger.info(f"📂 Data dir: {self.data_dir}")

    # ---------------------- Helpers ---------------------------
    @staticmethod
    def _sha256_bytes(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    @staticmethod
    def _today_path() -> str:
        now = dt.datetime.utcnow()
        return f"{now.year:04d}/{now.month:02d}/{now.day:02d}"

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Renombrado flexible para bolillas 1..6
        mapping = {}
        for col in df.columns:
            c = str(col).strip().lower()
            c = re.sub(r"[^a-z0-9_]+", "_", c)
            mapping[col] = c
        df = df.rename(columns=mapping)

        # Intentar detectar columnas de números 1..6
        posibles = []
        for key in df.columns:
            if re.search(r"(bolilla|n|num|number).*?1", key):
                posibles = [key]
                break

        # Si viene como bolilla_1...bolilla_6, mantener
        # si vienen como columnas genéricas, no forzar, solo validar si existen
        return df

    @staticmethod
    def _validate_numbers_row(row: Iterable[int], lower: int, upper: int) -> bool:
        try:
            nums = [int(x) for x in row]
        except Exception:
            return False
        if len(nums) < 6:
            return False
        # Rango y unicidad
        return all(lower <= n <= upper for n in nums[:6]) and (len(set(nums[:6])) == 6)

    def _store_with_metadata(self, name: str, df: pd.DataFrame, raw_bytes: Optional[bytes], source: SourceConfig) -> Dict[str, Any]:
        part = self._today_path() if self.partition_by_day else ""
        base = os.path.join(self.data_dir, name, part)
        os.makedirs(base, exist_ok=True)

        ts = dt.datetime.utcnow().isoformat()
        meta = {
            "dataset": name,
            "timestamp_utc": ts,
            "rows": int(df.shape[0]),
            "cols": list(map(str, df.columns)),
            "sha256": self._sha256_bytes(df.to_csv(index=False).encode("utf-8")),
            "source": asdict(source),
            "version": 1,
        }

        # Guardado principal
        if self.write_parquet:
            out_data = os.path.join(base, f"{name}.parquet")
            try:
                df.to_parquet(out_data, index=False)
            except Exception as e:
                logger.warning(f"Parquet no disponible, usando CSV.GZ: {e}")
                out_data = os.path.join(base, f"{name}.csv.gz")
                df.to_csv(out_data, index=False, compression="gzip")
        else:
            out_data = os.path.join(base, f"{name}.csv.gz")
            df.to_csv(out_data, index=False, compression="gzip")

        # Guardar metadatos
        out_meta = os.path.join(base, f"{name}.metadata.json")
        with open(out_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Guardar raw opcional
        if self.keep_raw and raw_bytes is not None:
            out_raw = os.path.join(base, f"{name}.raw")
            with open(out_raw, "wb") as f:
                f.write(raw_bytes)

        logger.info(f"✅ Guardado dataset {name} en {base}")
        return {"data_path": out_data, "meta_path": out_meta, "rows": meta["rows"]}

    # ---------------------- Fetchers --------------------------
    def _fetch_bytes(self, url: str, timeout: int) -> bytes:
        if not requests:
            raise RuntimeError("requests no disponible")
        headers = {"User-Agent": "OMEGA-DataMCP/1.0"}
        r = requests.get(url, timeout=timeout, headers=headers)
        r.raise_for_status()
        return r.content

    def _read_csv(self, b: bytes, delimiter: str, encoding: str) -> pd.DataFrame:
        bio = io.BytesIO(b)
        return pd.read_csv(bio, delimiter=delimiter, encoding=encoding)

    def _read_json(self, b: bytes, encoding: str) -> pd.DataFrame:
        s = b.decode(encoding or "utf-8")
        j = json.loads(s)
        if isinstance(j, list):
            return pd.DataFrame(j)
        elif isinstance(j, dict):
            # Si trae lista en alguna clave conocida
            for k, v in j.items():
                if isinstance(v, list):
                    return pd.DataFrame(v)
            return pd.DataFrame([j])
        else:
            raise ValueError("JSON no reconocido")

    # ---------------------- Pipeline --------------------------
    def ingest(self, sources: List[SourceConfig]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for src in sources:
            logger.info(f"🔎 Ingestando fuente: {src.name} ({src.kind})")
            raw: Optional[bytes] = None
            try:
                if src.url:
                    raw = self._fetch_bytes(src.url, src.timeout_seconds)
                elif src.local_path:
                    with open(src.local_path, "rb") as f:
                        raw = f.read()
                else:
                    raise ValueError("SourceConfig requiere url o local_path")

                if src.kind.lower() == "csv":
                    df = self._read_csv(raw, src.delimiter, src.encoding)
                elif src.kind.lower() in ("json", "api"):
                    df = self._read_json(raw, src.encoding)
                else:
                    raise ValueError(f"kind desconocido: {src.kind}")

                df = self._normalize_columns(df)

                # Validación básica de números si aplica
                if src.validate_numbers:
                    # Buscar columnas numéricas; intentar las 6 primeras
                    numeric_cols = [c for c in df.columns if re.search(r"(bolilla|n|num|number)_?\d+", c)]
                    if len(numeric_cols) >= 6:
                        sample = df[numeric_cols[:6]].values.tolist()
                        valid_rows = [self._validate_numbers_row(r, src.lower, src.upper) for r in sample]
                        valid_ratio = sum(valid_rows) / len(valid_rows) if sample else 0.0
                        if valid_ratio < 0.8:
                            logger.warning(f"⚠️ Ratio de filas válidas bajo ({valid_ratio:.2%}) en {src.name}. Revisar mapeo de columnas.")
                    else:
                        logger.warning("⚠️ No se detectaron 6 columnas de números, se omite validación estructural.")

                out = self._store_with_metadata(src.name, df, raw, src)
                results.append({"source": src.name, **out})
            except Exception as e:
                logger.error(f"🚨 Error ingesta {src.name}: {e}")
                results.append({"source": src.name, "error": str(e)})
            finally:
                gc.collect()
        return results


if __name__ == "__main__":
    # Demo local mínima
    mcp = ProductionLotteryDataMCP()
    # Ejemplo con archivo local CSV (ajusta la ruta)
    # res = mcp.ingest([SourceConfig(kind="csv", name="kabala_local", local_path="data/historial_kabala_github.csv")])
    # print(res)
    print("OK")
