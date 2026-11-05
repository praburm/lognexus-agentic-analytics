import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_curve, auc


def rule_based_predict(log):
    keywords = ["error", "fail", "exception", "fatal", "critical"]
    return 1 if any(k in log.lower() for k in keywords) else 0


def load_bgl_logs(log_file="data/BGL.log", max_lines=500000):
    labels = []
    messages = []
    count = 0

    with open(log_file, "r") as f:
        for line in f:
            if max_lines and count >= max_lines:
                break
            parts = line.strip().split()
            if len(parts) < 10:
                continue
            labels.append(0 if parts[0] == "-" else 1)
            messages.append(" ".join(parts[8:]))
            count += 1

    return messages, labels


def run_evaluation():
    print("Loading BGL logs...")
    documents, y = load_bgl_logs()

    split_index = int(0.7 * len(y))
    docs_train = documents[:split_index]
    docs_test  = documents[split_index:]
    y_train    = y[:split_index]
    y_test     = y[split_index:]

    print("Vectorizing using TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), min_df=2)
    X_train = vectorizer.fit_transform(docs_train)
    X_test  = vectorizer.transform(docs_test)

    print("Training Logistic Regression...")
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0)
    clf.fit(X_train, y_train)

    y_prob = clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob > 0.3).astype(int)
    y_pred_rule = [rule_based_predict(doc) for doc in docs_test]

    print("\nBGL Logistic Regression Results")
    print("Precision:", precision_score(y_test, y_pred))
    print("Recall:   ", recall_score(y_test, y_pred))
    print("F1-score: ", f1_score(y_test, y_pred))

    print("\nBGL Rule-Based Results")
    print("Precision:", precision_score(y_test, y_pred_rule))
    print("Recall:   ", recall_score(y_test, y_pred_rule))
    print("F1-score: ", f1_score(y_test, y_pred_rule))

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fpr_rule, tpr_rule, _ = roc_curve(y_test, y_pred_rule)

    return {
        "lr":   {"precision": precision_score(y_test, y_pred),
                 "recall": recall_score(y_test, y_pred),
                 "f1": f1_score(y_test, y_pred),
                 "fpr": fpr, "tpr": tpr, "auc": auc(fpr, tpr)},
        "rule": {"precision": precision_score(y_test, y_pred_rule),
                 "recall": recall_score(y_test, y_pred_rule),
                 "f1": f1_score(y_test, y_pred_rule),
                 "fpr": fpr_rule, "tpr": tpr_rule},
    }


if __name__ == "__main__":
    print(run_evaluation())
