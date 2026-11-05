from evaluation.evaluation_runner import run_evaluation as run_hdfs
from evaluation.bgl_evaluation import run_evaluation as run_bgl


def main():
    print("=" * 50)
    print("HDFS Log Anomaly Evaluation")
    print("=" * 50)
    run_hdfs()

    print("\n" + "=" * 50)
    print("BGL Log Anomaly Evaluation")
    print("=" * 50)
    run_bgl()


if __name__ == "__main__":
    main()
