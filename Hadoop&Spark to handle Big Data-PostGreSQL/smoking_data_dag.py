from __future__ import annotations

import datetime

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="smoking_data_pipeline",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["hadoop", "spark"],
    params={"file_name": "smoking_driking_dataset_Ver01.csv"},
) as dag:

    write_file_to_hadoop_docker = BashOperator(
        task_id="write_file_to_hadoop_docker",
        bash_command="docker cp /home/ftpuser/ftp/files/{{ params.file_name }} namenode:/data/{{ params.file_name }}"
    )

    write_file_to_hadoop_fs = BashOperator(
        task_id="write_file_to_hadoop_fs",
        bash_command="docker exec -it namenode hdfs dfs -put -f /data/{{ params.file_name }} /data/{{ params.file_name }}"
    )

    update_spark_codes = BashOperator(
        task_id="update_spark_codes",
        bash_command="docker cp /root/spark-code/. spark-master:/root/spark-scripts/"
    )

    run_spark_codes = BashOperator(
        task_id="run_spark_codes",
        bash_command="docker exec -it spark-master /spark/bin/spark-submit --master spark://spark-master:7077 --jars /root/spark-scripts/extra-jars/postgresql-42.7.0.jar /root/spark-scripts/smoking_data_transforms.py {{ params.file_name }}"
    )

    write_file_to_hadoop_docker >> write_file_to_hadoop_fs >> update_spark_codes >> run_spark_codes

if __name__ == "__main__":
    dag.test()