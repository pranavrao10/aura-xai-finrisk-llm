# LightGBM – v1
*Date generated:* 2025-07-12

## Thresholds chosen
| Split | F1-opt | Profit-opt |
|-------|-------:|-----------:|
| Train | 0.238 | – |
| Val   | 0.320 | 0.068 |

## Train (F1-optimised)
- **AUC:** `0.7359`  
- **PR-AUC:** `0.4576`  
- **KS:** `0.3390`  

```text
              precision    recall  f1-score   support

           0      0.879     0.725     0.794    901143
           1      0.363     0.611     0.456    231419

    accuracy                          0.702   1132562
   macro avg      0.621     0.668     0.625   1132562
weighted avg      0.774     0.702     0.725   1132562

```

## Validation (F1-optimised)
- **AUC:** `0.7791`  
- **PR-AUC:** `0.6662`  
- **KS:** `0.3961`  

```text
              precision    recall  f1-score   support

           0      0.843     0.746     0.792    130152
           1      0.503     0.650     0.568     51576

    accuracy                          0.719    181728
   macro avg      0.673     0.698     0.680    181728
weighted avg      0.747     0.719     0.728    181728

```

## Validation (Profit-optimised)
- **AUC:** `0.7791`  
- **PR-AUC:** `0.6662`  
- **KS:** `0.3961`  

```text
              precision    recall  f1-score   support

           0      0.935     0.218     0.354    130152
           1      0.328     0.962     0.489     51576

    accuracy                          0.429    181728
   macro avg      0.632     0.590     0.421    181728
weighted avg      0.763     0.429     0.392    181728

```
