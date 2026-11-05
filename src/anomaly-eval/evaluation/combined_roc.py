import matplotlib.pyplot as plt
from evaluation.evaluation_runner import run_evaluation as run_hdfs
from evaluation.bgl_evaluation import run_evaluation as run_bgl


def plot_combined_roc():
    print("Running HDFS Evaluation...")
    hdfs_results = run_hdfs()

    print("Running BGL Evaluation...")
    bgl_results = run_bgl()

    fpr_hdfs  = hdfs_results["lr"]["fpr"]
    tpr_hdfs  = hdfs_results["lr"]["tpr"]
    auc_hdfs  = hdfs_results["lr"]["auc"]

    fpr_bgl   = bgl_results["lr"]["fpr"]
    tpr_bgl   = bgl_results["lr"]["tpr"]
    auc_bgl   = bgl_results["lr"]["auc"]

    fpr_rule  = bgl_results["rule"]["fpr"]
    tpr_rule  = bgl_results["rule"]["tpr"]

    plt.figure(figsize=(6.5, 5))
    ax = plt.gca()
    ax.set_facecolor("#f7f7f7")

    plt.plot(fpr_hdfs, tpr_hdfs, linewidth=2.5, linestyle="-",
             label=f"HDFS LR (AUC = {auc_hdfs:.3f})")
    plt.plot(fpr_bgl,  tpr_bgl,  linewidth=2.5, linestyle="--",
             label=f"BGL LR (AUC = {auc_bgl:.3f})")
    plt.plot(fpr_rule, tpr_rule, linestyle="-.", linewidth=2, label="Rule-Based")
    plt.plot([0, 1], [0, 1], linestyle=":", linewidth=2, label="Random Classifier")

    plt.xlabel("False Positive Rate", fontsize=13, fontweight="bold")
    plt.ylabel("True Positive Rate",  fontsize=13, fontweight="bold")
    plt.title("ROC Curve Comparison: Baselines vs Proposed Setup",
              fontsize=14, fontweight="bold")
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.4)
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
    plt.legend(loc="lower right", fontsize=10, frameon=True)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.02])
    plt.tight_layout()
    plt.savefig("roc_comparison.pdf", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    plot_combined_roc()
