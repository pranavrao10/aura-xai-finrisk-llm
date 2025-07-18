# Logistic Regression – v1  
*Date generated:* 2025-07-18

## Thresholds chosen
| Split | F1-opt | Profit-opt |
|-------|-------:|-----------:|
| Train | 0.296 | – |
| Val | 0.253 | 0.115 |

## Train (F1-optimised)
- **AUC:** `0.7010`  
- **PR-AUC:** `0.3603`  
- **KS:** `0.2908`  

```text
              precision    recall  f1-score   support

           0      0.874     0.659     0.751    901143
           1      0.322     0.631     0.426    231419

    accuracy                          0.653   1132562
   macro avg      0.598     0.645     0.589   1132562
weighted avg      0.761     0.653     0.685   1132562

```

## Validation (F1-optimised)
- **AUC:** `0.6664`  
- **PR-AUC:** `0.4122`  
- **KS:** `0.2409`  

```text
              precision    recall  f1-score   support

           0      0.838     0.460     0.594    130152
           1      0.363     0.775     0.494     51576

    accuracy                          0.549    181728
   macro avg      0.600     0.618     0.544    181728
weighted avg      0.703     0.549     0.565    181728

```

## Validation (Profit-optimised)
- **AUC:** `0.6664`  
- **PR-AUC:** `0.4122`  
- **KS:** `0.2409`  

```text
              precision    recall  f1-score   support

           0      0.915     0.147     0.253    130152
           1      0.310     0.965     0.469     51576

    accuracy                          0.379    181728
   macro avg      0.612     0.556     0.361    181728
weighted avg      0.743     0.379     0.314    181728

```
