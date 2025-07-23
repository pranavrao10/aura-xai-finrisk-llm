
---

## Test results
| Threshold type | Value |
|----------------|------:|
| F1-opt | 0.216 |
| Profit-opt | 0.095 |

### Test (F1-optimised)
- **AUC:** `0.6528`  
- **PR-AUC:** `0.4145`  
- **KS:** `0.2276`  

```text
              precision    recall  f1-score   support

           0      0.815     0.463     0.590     47444
           1      0.380     0.759     0.507     20617

    accuracy                          0.553     68061
   macro avg      0.598     0.611     0.549     68061
weighted avg      0.684     0.553     0.565     68061

```

### Test (Profit-optimised)
- **AUC:** `0.6528`  
- **PR-AUC:** `0.4145`  
- **KS:** `0.2276`  

```text
              precision    recall  f1-score   support

           0      0.895     0.124     0.218     47444
           1      0.324     0.966     0.485     20617

    accuracy                          0.379     68061
   macro avg      0.609     0.545     0.351     68061
weighted avg      0.722     0.379     0.299     68061

```
