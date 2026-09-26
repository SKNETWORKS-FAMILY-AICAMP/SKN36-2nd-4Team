import pandas as pd

path = r"C:\dev\project\riot_churn_vscode_bundle\lol_churn_project\06_ml_features.csv"

df = pd.read_csv(path)

print("데이터 크기:", df.shape)

print("\nchurn 개수")
print(df["churn"].value_counts())

print("\nchurn 비율")
print(df["churn"].value_counts(normalize=True))