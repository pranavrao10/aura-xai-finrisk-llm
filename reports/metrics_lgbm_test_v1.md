# LightGBM – Test metrics (v1)
*Date generated:* 2025-07-12

## Thresholds
| Optimisation | Threshold |
|--------------|-----------:|
| F1           | 0.574 |
| Profit       | 0.122 |

### Test (F1-optimised)
- **AUC:** `0.8714`  
- **PR-AUC:** `0.8349`  
- **KS:** `0.5889`  

```text
              precision    recall  f1-score   support

           0      0.851     0.976     0.909     47444
           1      0.916     0.606     0.729     20617

    accuracy                          0.864     68061
   macro avg      0.884     0.791     0.819     68061
weighted avg      0.871     0.864     0.855     68061

```

### Test (Profit-optimised)
- **AUC:** `0.8714`  
- **PR-AUC:** `0.8349`  
- **KS:** `0.5889`  

```text
              precision    recall  f1-score   support

           0      0.936     0.409     0.569     47444
           1      0.407     0.935     0.568     20617

    accuracy                          0.568     68061
   macro avg      0.671     0.672     0.568     68061
weighted avg      0.776     0.568     0.569     68061

```
