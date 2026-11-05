import re
import pandas as pd
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    accuracy_score, confusion_matrix, roc_curve, auc,
)


def rule_based_predict(log):
    keywords = ["error", "fail", "exception", "fatal", "critical"]
    return 1 if any(k in log.lower() for k in keywords) else 0


def load_hdfs_logs(log_file="data/HDFS.log", max_lines=500000):
    block_logs = defaultdict(list)
    count = 0

    with open(log_file, "r") as f:
        for line in f:
            if max_lines and count >= max_lines:
                break
            match = re.search(r"(blk_-?\d+)", line)
            if match:
                block_logs[match.group(1)].append(line.strip())
            count += 1

    return block_logs


def run_evaluation():
    print("Loading HDFS logs...")
    block_logs = load_hdfs_logs()

    print("Loading labels...")
    labels_df = pd.read_csv("data/anomaly_label.csv")
    labels_df["Label"] = labels_df["Label"].map({"Normal": 0, "Anomaly": 1})
    labels_dict = dict(zip(labels_df["BlockId"], labels_df["Label"]))

    documents = []
    y = []
    for block_id, logs in block_logs.items():
        if block_id not in labels_dict:
            continue
        documents.append(" ".join(logs))
        y.append(labels_dict[block_id])

    print("Vectorizing using TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), min_df=2)
    X = vectorizer.fit_transform(documents)

    # stratified split to preserve anomaly ratio across train/test sets
    X_train, X_test, y_train, y_test, docs_train, docs_test = train_test_split(
        X, y, documents, test_size=0.3, random_state=42, stratify=y
    )

    print("Training Logistic Regression...")
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    print("\nHDFS Logistic Regression Results")
    print("Precision:", precision_score(y_test, y_pred))
    print("Recall:   ", recall_score(y_test, y_pred))
    print("F1-score: ", f1_score(y_test, y_pred))
    print("Accuracy: ", accuracy_score(y_test, y_pred))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    print("AUC Score:", roc_auc)

    print("\nRunning Rule-Based Baseline...")
    y_pred_rule = [rule_based_predict(doc) for doc in docs_test]

    print("\nHDFS Rule-Based Results")
    print("Precision:", precision_score(y_test, y_pred_rule))
    print("Recall:   ", recall_score(y_test, y_pred_rule))
    print("F1-score: ", f1_score(y_test, y_pred_rule))

    fpr_rule, tpr_rule, _ = roc_curve(y_test, y_pred_rule)

    return {
        "lr":   {"precision": precision_score(y_test, y_pred),
                 "recall": recall_score(y_test, y_pred),
                 "f1": f1_score(y_test, y_pred),
                 "auc": roc_auc, "fpr": fpr, "tpr": tpr},
        "rule": {"precision": precision_score(y_test, y_pred_rule),
                 "recall": recall_score(y_test, y_pred_rule),
                 "f1": f1_score(y_test, y_pred_rule),
                 "fpr": fpr_rule, "tpr": tpr_rule},
    }


if __name__ == "__main__":
    print(run_evaluation())
