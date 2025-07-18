# Logistic Regression – v1  
*Date generated:* 2025-07-12

## Thresholds chosen
| Split | F1-opt | Profit-opt |
|-------|-------:|-----------:|
| Train | 0.236 | – |
| Val | 0.299 | 0.114 |

## Train (F1-optimised)
- **AUC:** `0.7390`  
- **PR-AUC:** `0.4498`  
- **KS:** `0.3449`  

```text
              precision    recall  f1-score   support

           0      0.878     0.742     0.804    901143
           1      0.373     0.597     0.459    231419

    accuracy                          0.712   1132562
   macro avg      0.625     0.669     0.631   1132562
weighted avg      0.774     0.712     0.733   1132562

```

## Validation (F1-optimised)
- **AUC:** `0.7834`  
- **PR-AUC:** `0.6600`  
- **KS:** `0.4027`  

```text
              precision    recall  f1-score   support

           0      0.837     0.791     0.813    130152
           1      0.536     0.612     0.572     51576

    accuracy                          0.740    181728
   macro avg      0.687     0.701     0.692    181728
weighted avg      0.752     0.740     0.745    181728

```

## Validation (Profit-optimised)
- **AUC:** `0.7834`  
- **PR-AUC:** `0.6600`  
- **KS:** `0.4027`  

```text
              precision    recall  f1-score   support

           0      0.932     0.256     0.401    130152
           1      0.336     0.953     0.497     51576

    accuracy                          0.453    181728
   macro avg      0.634     0.604     0.449    181728
weighted avg      0.763     0.453     0.428    181728

```
