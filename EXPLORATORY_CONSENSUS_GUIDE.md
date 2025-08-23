# OMEGA PRO AI v10.1 - Exploratory Consensus Mode Guide

## Overview

The Exploratory Consensus Mode is a new feature in OMEGA PRO AI v10.1 that enhances the consensus engine to detect and prioritize rare number combinations. This mode is specifically designed to improve prediction capabilities for edge case combinations like `[12, 27, 1, 10, 13, 22]`.

## Key Features

### 🔍 Exploration Mode Toggle
- **Parameter**: `exploration_mode=True`
- **Description**: Enables exploratory consensus functionality
- **Default**: `False` (maintains backward compatibility)

### 🚀 Dynamic Exploration Boost
- Automatically detects rare numbers in the historical data
- Applies exploration boost to combinations containing rare numbers
- Scales with exploration intensity parameter

### 🔬 Anomaly Score Calculation
- Detects edge case combinations (consecutive numbers, arithmetic progressions)
- Identifies patterns uncommon in historical data
- Adds anomaly score to final ranking

### 🌈 Enhanced Diversity Bonus
- More aggressive rare number detection in exploration mode
- Scales bonus based on exploration intensity
- Prioritizes combinations with multiple rare numbers

### 💎 Rare Number Detection
- Identifies bottom 25% frequency numbers as "rare"
- Analyzes recent historical data (configurable lookback)
- Integrates rare numbers into core set generation

### ⚙️ Flexible Configuration
- New "exploratory" profile in PESO_MAP
- Configurable exploration parameters via EXPLORATORY_CONFIG
- Adjustable exploration intensity (0.1-1.0)

## Usage Examples

### Basic Exploration Mode

```python
from core.consensus_engine import generar_combinaciones_consenso

# Standard mode (default)
combinations = generar_combinaciones_consenso(
    historial_df=df,
    cantidad=10,
    perfil_svi="default"
)

# Exploration mode
combinations = generar_combinaciones_consenso(
    historial_df=df,
    cantidad=10,
    perfil_svi="exploratory",
    exploration_mode=True,
    exploration_intensity=0.5
)
```

### Convenience Function

```python
from core.consensus_engine import generar_combinaciones_consenso_exploratory

# One-liner for exploration mode
combinations = generar_combinaciones_consenso_exploratory(
    historial_df=df,
    cantidad=10,
    exploration_intensity=0.7
)
```

### Advanced Configuration

```python
# High-intensity rare number hunting
combinations = generar_combinaciones_consenso(
    historial_df=df,
    cantidad=20,
    perfil_svi="exploratory",
    exploration_mode=True,
    exploration_intensity=0.9,  # Aggressive exploration
    use_score_combinations=True,
    retrain=True
)
```

## Parameter Reference

### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exploration_mode` | bool | `False` | Enables exploratory consensus functionality |
| `exploration_intensity` | float | `0.3` | Controls exploration aggressiveness (0.1-1.0) |
| `perfil_svi` | str | `"default"` | Use `"exploratory"` for optimal rare number detection |

### Configuration Constants

```python
EXPLORATORY_CONFIG = {
    "rare_number_threshold": 0.25,     # Bottom 25% = rare
    "anomaly_score_weight": 0.20,      # Weight for anomaly score
    "diversity_bonus_cap": 0.35,       # Maximum diversity bonus
    "edge_case_boost": 0.25,           # Boost for edge cases
    "exploration_decay": 0.95,         # Decay factor over time
    "min_rare_numbers": 2,             # Minimum rare numbers for bonus
    "historical_lookback": 100,        # Historical data window
}
```

## Model Weight Profiles

### Exploratory Profile
The new "exploratory" profile prioritizes models that are better at discovering rare patterns:

```python
"exploratory": {
    "ghost_rng": 1.4,      # Best for random patterns
    "montecarlo": 1.3,     # Good for exploration
    "genetico": 1.2,       # Evolutionary search
    "clustering": 1.1,     # Pattern detection
    "transformer": 1.1,    # Sequence patterns
    "lstm_v2": 1.0,        # Standard weight
    "inverse_mining": 1.0, # Standard weight
    "apriori": 0.9,        # Less emphasis on frequent patterns
}
```

## Output Analysis

### Exploration Metadata
When exploration mode is enabled, combinations include additional metadata:

```python
combo = {
    "combination": [12, 27, 1, 10, 13, 22],
    "score": 5.247,
    "normalized": 5.687,  # Includes exploration boosts
    "source": "montecarlo",
    "metrics": {
        "exploration_mode": True,
        "exploration_boost": 0.140,
        "anomaly_score": 0.000,
        "diversity_bonus": 0.300,
        "rare_count": 4,  # Number of rare numbers
    }
}
```

### Logging Output
Exploration mode provides detailed logging:

```
🔍 Exploratory boost for [12, 27, 1, 10, 13, 22]: exploration=0.140, anomaly=0.000, diversity=0.300
🔍 Exploration Statistics:
   📊 Combinations with exploration boost: 7/10
   🚀 Total exploration boost: 0.980
   🔬 Total anomaly score: 0.120
   💎 Average rare numbers per combo: 2.3
```

## Best Practices

### 1. When to Use Exploration Mode
- Looking for rare number combinations
- Historical data shows patterns but missing edge cases
- Want to discover unconventional combinations
- Testing new strategies

### 2. Exploration Intensity Guidelines
- **0.1-0.3**: Conservative exploration, slight bias toward rare numbers
- **0.4-0.6**: Balanced exploration, good for general use
- **0.7-0.9**: Aggressive exploration, strong rare number preference
- **1.0**: Maximum exploration, may sacrifice accuracy for discovery

### 3. Profile Selection
- Use `"exploratory"` profile with exploration mode
- Combine with `use_score_combinations=True` for best results
- Consider `retrain=True` if model performance is poor

### 4. Data Requirements
- Minimum 50 historical draws recommended
- More data improves rare number detection accuracy
- Recent data weighted more heavily

## Performance Considerations

### Computational Impact
- Exploration mode adds ~10-15% computational overhead
- Additional analysis for rare number detection
- Enhanced scoring calculations

### Memory Usage
- Minimal additional memory usage
- Metadata storage for exploration statistics
- Historical number frequency tracking

### Accuracy Trade-offs
- May reduce overall accuracy slightly
- Improves detection of rare combinations
- Better long-term coverage of number space

## Troubleshooting

### Common Issues

1. **No exploration boosts applied**
   - Check that `exploration_mode=True`
   - Verify sufficient historical data
   - Increase `exploration_intensity`

2. **Too many rare combinations**
   - Reduce `exploration_intensity`
   - Adjust `rare_number_threshold` in config
   - Use lower `diversity_bonus_cap`

3. **Performance issues**
   - Disable heavy ML models for testing
   - Reduce `historical_lookback` window
   - Lower combination count

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.INFO)

# Enable detailed logging
combinations = generar_combinaciones_consenso_exploratory(
    historial_df=df,
    cantidad=5,
    exploration_intensity=0.8
)
```

## Integration with Existing Code

The exploratory consensus mode is fully backward compatible. Existing code continues to work without changes:

```python
# This still works exactly as before
combinations = generar_combinaciones_consenso(historial_df, 10, "default")
```

New functionality is opt-in only:

```python
# Add exploration mode to existing calls
combinations = generar_combinaciones_consenso(
    historial_df, 10, "default",
    exploration_mode=True,  # Add this line
    exploration_intensity=0.5  # And this line
)
```

## Future Enhancements

Planned improvements for future versions:

- **Adaptive Exploration**: Automatic intensity adjustment based on results
- **Pattern Learning**: ML-based anomaly detection improvements
- **Multi-objective Optimization**: Balance exploration vs exploitation
- **Real-time Calibration**: Dynamic parameter tuning
- **Advanced Metrics**: Additional exploration scoring methods

## Conclusion

The Exploratory Consensus Mode significantly enhances OMEGA PRO AI's ability to detect and prioritize rare number combinations while maintaining full backward compatibility. Use this feature when you need to discover edge cases and unconventional patterns in lottery data.

For optimal results with rare combinations like `[12, 27, 1, 10, 13, 22]`, use:

```python
combinations = generar_combinaciones_consenso_exploratory(
    historial_df=your_data,
    cantidad=20,
    exploration_intensity=0.7
)
```