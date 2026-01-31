import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

df = pd.read_csv(r"C:\Users\dell\OneDrive\Desktop\MINOR\LocalModels\Hospital2\Dataset_Hospital2.csv")
df_50 = df.head(50)



X=df.drop('target', axis=1)
Y= df_50['target']

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter= 10000)
model.fit(X_train, Y_train)

Y_pred = model.predict(X_test)
print("accuracy: ", accuracy_score(Y_test, Y_pred))
print("\cofusion Matrix: \n, confusion_matrix(Y_test, Y_pred)")
print("\nClassification Report: \n", classification_report(Y_test, Y_pred))

joblib.dump(model, r"C:\Users\dell\OneDrive\Desktop\MINOR\LocalModels\Hospital2\logistic_regression_model_hospital2.pkl")
print("\n💾 Model saved as logistic_model_weights.pkl")
weights = pd.DataFrame({"feature":X.columns, "Coffiecients": model.coef_[0]})
weights.loc[len(weights)] = ["intercept", model.intercept_[0]]
weights.to_csv(r"C:\Users\dell\OneDrive\Desktop\MINOR\LocalModels\Hospital2\Hospital2weights.csv", index=False)
print("Numeric weights saved to Hospital2weights.csv")
