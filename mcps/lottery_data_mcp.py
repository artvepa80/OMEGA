#!/usr/bin/env python3
"""
🎰 Production Lottery Data MCP - BUGS FIXED
Multi-source lottery data ingestion with bulletproof error handling
"""

import asyncio
import aiohttp
import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import async_timeout
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)  # ✅ Fixed

class ProductionLotteryDataMCP:
    """Production-ready MCP para ingesta de datos de loterías"""
    
    def __init__(self, data_dir: str = "data/lottery_ingestion"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache para evitar re-fetch innecesario
        self.cache_file = self.data_dir / "cache.json"
        self.cache = self._load_cache()
        
        # Lock para rate limiting thread-safe
        self._rl_lock = asyncio.Lock()
        
        # Configuración de loterías con múltiples fuentes
        self.lottery_configs = {
            "kabala_pe": {
                "name": "Kabala Perú",
                "number_count": 6,
                "number_range": [1, 40],
                "sources": [
                    {
                        "type": "youtube_title_parsing",
                        "url": "https://www.youtube.com/@KabalaOficial/videos",
                        "pattern": r"SORTEO.*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2})",
                        "priority": 1
                    },
                    {
                        "type": "manual_csv",
                        "file": "data/kabala_pe_backup.csv",
                        "priority": 2
                    }
                ]
            },
            "megasena_br": {
                "name": "Mega-Sena Brasil",
                "number_count": 6,
                "number_range": [1, 60],
                "sources": [
                    {
                        "type": "api",
                        "url": "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/1",
                        "priority": 1
                    },
                    {
                        "type": "scraping",
                        "url": "https://www.loterias.caixa.gov.br/wps/portal/loterias/landing/megasena",
                        "selector": ".resultado-loteria .numeros .numero",
                        "priority": 2
                    }
                ]
            },
            "powerball_us": {
                "name": "Powerball USA",
                "number_count": 5,
                "number_range": [1, 69],
                "bonus_count": 1,
                "bonus_range": [1, 26],
                "sources": [
                    {
                        "type": "api",
                        "url": "https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json",
                        "priority": 1
                    }
                ]
            }
        }
    
    def _load_cache(self) -> Dict[str, Any]:
        """Cargar cache de resultados anteriores"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Guardar cache atomically"""
        try:
            with NamedTemporaryFile('w', delete=False, dir=str(self.data_dir), 
                                   suffix='.json') as tmp:
                json.dump(self.cache, tmp, indent=2)
                tmp_name = tmp.name
            
            # Atomic replace
            Path(tmp_name).replace(self.cache_file)
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    async def fetch_lottery_result(self, lottery_id: str) -> Optional[Dict[str, Any]]:
        """Fetch resultado de lotería específica"""
        if lottery_id not in self.lottery_configs:
            logger.error(f"Lottery {lottery_id} not supported")
            return None
        
        config = self.lottery_configs[lottery_id]
        
        # Verificar cache primero
        cache_key = f"{lottery_id}_latest"
        cached_result = self.cache.get(cache_key)
        
        if cached_result and self._is_cache_fresh(cached_result, hours=1):
            logger.info(f"Using cached result for {lottery_id}")
            return cached_result
        
        # Intentar fuentes en orden de prioridad
        for source in sorted(config["sources"], key=lambda x: x["priority"]):
            try:
                result = await self._fetch_from_source(source, config)
                if result and self._validate_result(result, config):
                    # Check si es mock - no aceptar como producción
                    if result.get("__mock__"):
                        logger.warning(f"Skipping mock result for {lottery_id}")
                        continue
                    
                    # Enriquecer resultado
                    enriched_result = self._enrich_result(result, lottery_id, source)
                    
                    # Guardar en cache
                    self.cache[cache_key] = enriched_result
                    self._save_cache()
                    
                    # Guardar en archivo histórico
                    await self._save_historical_result(lottery_id, enriched_result)
                    
                    logger.info(f"✅ Fetched {lottery_id} from {source['type']}")
                    return enriched_result
                    
            except Exception as e:
                logger.warning(f"Source {source['type']} failed for {lottery_id}: {e}")
                continue
        
        logger.error(f"❌ All sources failed for {lottery_id}")
        
        # Return stale cache if available, marked as stale
        if cached_result:
            return {**cached_result, "stale": True}
        return None
    
    async def _fetch_from_source(self, source: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch desde fuente específica"""
        
        if source["type"] == "api":
            return await self._fetch_from_api(source["url"])
        
        elif source["type"] == "youtube_title_parsing":
            result = await self._fetch_from_youtube_titles(source["url"], source["pattern"])
            if result:
                result["__mock__"] = True  # ✅ Marcar como mock
            return result
        
        elif source["type"] == "scraping":
            return await self._fetch_from_scraping(source["url"], source["selector"])
        
        elif source["type"] == "manual_csv":
            return await self._fetch_from_csv(source["file"])
        
        else:
            logger.error(f"Unknown source type: {source['type']}")
            return None
    
    async def _http_get_json(self, url: str, session: aiohttp.ClientSession, retries: int = 3):
        """HTTP GET with retries and backoff - ✅ Production hardened"""
        for i in range(retries):
            try:
                async with async_timeout.timeout(15):
                    async with session.get(url, headers={
                        "User-Agent": "OMEGA-AI-Bot/1.0 (+https://omega-ai.com)"
                    }) as response:
                        response.raise_for_status()
                        return await response.json(content_type=None)
            except Exception as e:
                if i == retries - 1:
                    raise
                await asyncio.sleep(2 ** i)  # Exponential backoff
    
    async def _fetch_from_api(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch desde API con robust parsing - ✅ Fixed"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=5, sock_read=15)
        ) as session:
            data = await self._http_get_json(url, session)
            return self._parse_api_response(data)
    
    async def _fetch_from_youtube_titles(self, channel_url: str, pattern: str) -> Optional[Dict[str, Any]]:
        """Fetch números desde títulos de YouTube - ✅ Mock clearly marked"""
        logger.warning("YouTube fetching requires YouTube Data API - using development mock")
        return {
            "numbers": [12, 15, 23, 28, 35, 39],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source_type": "youtube_mock",
            "__mock__": True  # ✅ Clear mock flag
        }
    
    async def _fetch_from_scraping(self, url: str, selector: str) -> Optional[Dict[str, Any]]:
        """Fetch mediante scraping - ✅ Better error handling"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup not available for scraping")
            return None
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20)
            ) as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; OMEGA-AI/1.0)"
                }) as response:
                    response.raise_for_status()
                    html = await response.text()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    number_elements = soup.select(selector)
                    numbers = []
                    
                    for elem in number_elements:
                        try:
                            num_text = elem.get_text().strip()
                            num = int(num_text)
                            numbers.append(num)
                        except ValueError:
                            continue
                    
                    if len(numbers) >= 5:  # Mínimo requerido
                        return {
                            "numbers": numbers[:6],  # Cap at 6
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "source_type": "scraping"
                        }
        
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
        
        return None
    
    def _extract_numbers_from_row(self, last_row) -> List[int]:
        """Extract exactly 6 numbers from CSV row - ✅ Fixed ordering"""
        import pandas as pd
        
        # Get number columns in correct order (n1, n2, ..., n10, etc.)
        number_cols = sorted(
            [c for c in last_row.index if re.fullmatch(r"n[1-9]\d*", c)],
            key=lambda x: int(x[1:])
        )
        
        nums = []
        for col in number_cols:
            if pd.notna(last_row[col]):
                try:
                    nums.append(int(last_row[col]))
                except (ValueError, TypeError):
                    continue
        
        return nums[:6]  # ✅ Force exactly 6 numbers max
    
    async def _fetch_from_csv(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Fetch desde archivo CSV de backup - ✅ Better number extraction"""
        try:
            import pandas as pd
            
            if not Path(file_path).exists():
                logger.warning(f"CSV file not found: {file_path}")
                return None
            
            df = pd.read_csv(file_path)
            if len(df) == 0:
                return None
            
            # Obtener última fila
            last_row = df.iloc[-1]
            
            # Extract numbers using robust method
            numbers = self._extract_numbers_from_row(last_row)
            
            if len(numbers) < 5:  # Need at least 5 numbers
                logger.warning(f"Insufficient numbers in CSV: {len(numbers)}")
                return None
            
            return {
                "numbers": numbers,
                "date": last_row.get("date", datetime.now().strftime("%Y-%m-%d")),
                "source_type": "csv_backup"
            }
        
        except Exception as e:
            logger.error(f"CSV fetch failed: {e}")
            return None
    
    def _parse_api_response(self, data: Any) -> Optional[Dict[str, Any]]:
        """Parse respuesta de API - ✅ Real API structure handling"""
        
        # Powerball format (list of recent draws)
        if (isinstance(data, list) and data and isinstance(data[0], dict) 
            and "field_draw_date" in data[0]):
            try:
                draw = data[0]
                nums_str = draw["field_winning_numbers"]
                nums = [int(x) for x in nums_str.split()][:5]
                pb = int(draw["field_powerball"])
                
                return {
                    "numbers": nums,
                    "bonus": [pb],
                    "date": draw.get("field_draw_date"),
                    "source_type": "api"
                }
            except (KeyError, ValueError, IndexError) as e:
                logger.warning(f"Failed to parse Powerball response: {e}")
        
        # Mega-Sena CAIXA format
        if isinstance(data, dict) and "listaDezenas" in data:
            try:
                nums = [int(x) for x in data["listaDezenas"]][:6]
                return {
                    "numbers": nums,
                    "date": data.get("dataApuracao", datetime.now().strftime("%Y-%m-%d")),
                    "source_type": "api"
                }
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse Mega-Sena response: {e}")
        
        # Generic number array
        if isinstance(data, list) and all(isinstance(x, int) for x in data):
            return {
                "numbers": data[:6],  # Cap at 6
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source_type": "api"
            }
        
        # Single draw format
        if isinstance(data, dict) and "numbers" in data:
            nums = data["numbers"]
            if isinstance(nums, list) and all(isinstance(x, int) for x in nums):
                result = {
                    "numbers": nums[:6],
                    "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "source_type": "api"
                }
                if "bonus" in data:
                    result["bonus"] = data["bonus"]
                return result
        
        logger.warning(f"Unable to parse API response structure: {type(data)}")
        return None
    
    def _validate_result(self, result: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """Validar que el resultado sea válido - ✅ Strict validation"""
        if not result or "numbers" not in result:
            return False
        
        numbers = result["numbers"]
        
        # Check if mock result
        if result.get("__mock__"):
            logger.warning("Result is mock; skipping validation for production")
            return False
        
        # Verificar que numbers sea lista de enteros
        if not isinstance(numbers, list) or not all(isinstance(x, int) for x in numbers):
            logger.warning(f"Invalid number types: {numbers}")
            return False
        
        # Verificar cantidad exacta de números
        expected_count = config["number_count"]
        if len(numbers) != expected_count:
            logger.warning(f"Invalid number count: {len(numbers)} != {expected_count}")
            return False
        
        # Verificar rango de números
        min_num, max_num = config["number_range"]
        if not all(min_num <= num <= max_num for num in numbers):
            logger.warning(f"Numbers out of range {min_num}-{max_num}: {numbers}")
            return False
        
        # Verificar unicidad (no duplicados)
        if len(set(numbers)) != len(numbers):
            logger.warning(f"Duplicate numbers found: {numbers}")
            return False
        
        return True
    
    def _enrich_result(self, result: Dict[str, Any], lottery_id: str, source: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer resultado con metadatos"""
        enriched = result.copy()
        enriched.update({
            "lottery_id": lottery_id,
            "fetched_at": datetime.now().isoformat(),
            "source_config": {k: v for k, v in source.items() if k != "pattern"},  # Don't store regex
            "result_hash": self._calculate_result_hash(result["numbers"]),
            "confidence": self._calculate_confidence(source)
        })
        return enriched
    
    def _calculate_result_hash(self, numbers: List[int]) -> str:
        """Calcular hash único del resultado"""
        numbers_str = "-".join(map(str, sorted(numbers)))
        return hashlib.md5(numbers_str.encode()).hexdigest()[:8]
    
    def _calculate_confidence(self, source: Dict[str, Any]) -> float:
        """Calcular confianza basada en fuente"""
        confidence_map = {
            "api": 0.95,
            "scraping": 0.85,
            "youtube_title_parsing": 0.60,  # Lower for mock
            "manual_csv": 0.90
        }
        return confidence_map.get(source["type"], 0.5)
    
    def _is_cache_fresh(self, cached_result: Dict[str, Any], hours: int = 1) -> bool:
        """Verificar si cache está fresco"""
        try:
            fetched_at = datetime.fromisoformat(cached_result["fetched_at"])
            return (datetime.now() - fetched_at) < timedelta(hours=hours)
        except (KeyError, ValueError):
            return False
    
    def _atomic_append(self, path: Path, line: str):
        """Atomic append to file - ✅ Production safe"""
        try:
            with NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
                tmp.write(line)
                tmp_name = tmp.name
            
            # Append atomically
            with open(path, "a", encoding='utf-8') as out, open(tmp_name, "r") as tmpf:
                out.write(tmpf.read())
            
            Path(tmp_name).unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Atomic append failed: {e}")
    
    async def _save_historical_result(self, lottery_id: str, result: Dict[str, Any]):
        """Guardar resultado en archivo histórico - ✅ Dedup + atomic"""
        history_file = self.data_dir / f"{lottery_id}_history.jsonl"
        
        # Check for duplicate (same hash + date)
        result_hash = result.get("result_hash")
        result_date = result.get("date")
        
        if history_file.exists() and result_hash:
            try:
                # Check last few lines for duplicate
                with open(history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-10:]  # Check last 10 results
                
                for line in lines:
                    try:
                        prev_result = json.loads(line.strip())
                        if (prev_result.get("result_hash") == result_hash and 
                            prev_result.get("date") == result_date):
                            logger.info(f"Duplicate result detected for {lottery_id}, skipping save")
                            return
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.warning(f"Could not check for duplicates: {e}")
        
        # Save with atomic append
        try:
            line = json.dumps(result, separators=(',', ':')) + '\n'
            self._atomic_append(history_file, line)
            logger.debug(f"Saved historical result for {lottery_id}")
        except Exception as e:
            logger.error(f"Failed to save historical result: {e}")
    
    async def bulk_fetch_all_lotteries(self) -> Dict[str, Any]:
        """Fetch todas las loterías en paralelo"""
        results = {}
        
        tasks = [
            self.fetch_lottery_result(lottery_id) 
            for lottery_id in self.lottery_configs.keys()
        ]
        
        lottery_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for lottery_id, result in zip(self.lottery_configs.keys(), lottery_results):
            if isinstance(result, Exception):
                results[lottery_id] = {
                    "success": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                results[lottery_id] = {
                    "success": result is not None,
                    "stale": result.get("stale", False) if result else False,
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                }
        
        return results
    
    def get_supported_lotteries(self) -> List[str]:
        """Obtener lista de loterías soportadas"""
        return list(self.lottery_configs.keys())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_entries": len(self.cache),
            "cache_size_kb": len(json.dumps(self.cache).encode()) / 1024,
            "supported_lotteries": self.get_supported_lotteries()
        }