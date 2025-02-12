from pyspark.sql import SparkSession
import sys

file = sys.argv[1]

mode = "overwrite"
url = "jdbc:postgresql://db.wofgelelqdddhxoyxxhb.supabase.co:5432/postgres"
properties = {"user": "postgres","password": "081RqzO4o9mRepc5","driver": "org.postgresql.Driver"}

spark = SparkSession.builder.appName("Smoking Data").getOrCreate()

spark.read.option("header",True) \
    .csv("hdfs://namenode:9000/data/" + file) \
    .createOrReplaceTempView("smoking_data")

sight_df = spark.sql("""
    SELECT 
    SMK_stat_type_cd,
    DRK_YN,
    avg(sight_left),
    avg(sight_right)
    FROM smoking_data
    group by SMK_stat_type_cd, DRK_YN;
""")

sight_df.write.jdbc(url=url, table="sight_table", mode=mode, properties=properties)

hearing_df = spark.sql("""
    SELECT
    SMK_stat_type_cd,
    DRK_YN,
    case
    when hear_left = 2 or hear_right = 2 then 'abnormal'
    else 'normal'
    end as hearing,
    count(*)
    FROM smoking_data
    group by SMK_stat_type_cd, DRK_YN, hearing;
""")

hearing_df.write.jdbc(url=url, table="hearing_table", mode=mode, properties=properties)

bmi_vs_chole = spark.sql("""
SELECT BMI_category, AVG(Tot_chole) AS avg_cholesterol
FROM (
    SELECT height, weight, Tot_chole,
           CASE 
               WHEN (weight / POWER(height/100, 2)) < 18.5 THEN 'Underweight'
               WHEN (weight / POWER(height/100, 2)) BETWEEN 18.5 AND 24.9 THEN 'Normal'
               WHEN (weight / POWER(height/100, 2)) BETWEEN 25 AND 29.9 THEN 'Overweight'
               ELSE 'Obese'
           END AS BMI_category
    FROM smoking_data
)
GROUP BY BMI_category;
""")

bmi_vs_chole.write.jdbc(url=url, table="bmi_vs_chole", mode=mode, properties=properties)

bmi_vs_smoke = spark.sql("""
SELECT
SMK_stat_type_cd,
CASE 
               WHEN (weight / POWER(height/100, 2)) < 18.5 THEN 'Underweight'
               WHEN (weight / POWER(height/100, 2)) BETWEEN 18.5 AND 24.9 THEN 'Normal'
               WHEN (weight / POWER(height/100, 2)) BETWEEN 25 AND 29.9 THEN 'Overweight'
               ELSE 'Obese'
           END AS BMI_category,
count(*)
FROM smoking_data
group by SMK_stat_type_cd, BMI_category;
""")

bmi_vs_smoke.write.jdbc(url=url, table="bmi_vs_smoke", mode=mode, properties=properties)

age_groups = spark.sql("""
SELECT
case
when age between 20 and 35 then 'young adults'
when age between 36 and 50 then 'adults'
when age between 51 and 70 then 'middle age adults'
else 'senior adults'
end as age_group,
count(*)
FROM smoking_data
group by age_group;
""")

age_groups.write.jdbc(url=url, table="age_groups", mode=mode, properties=properties)

alcohol_consumption = spark.sql("""
SELECT 
    DRK_YN,
    AVG(SGOT_AST) AS avg_SGOT_AST,
    AVG(SGOT_ALT) AS avg_SGOT_ALT,
    AVG(gamma_GTP) AS avg_gamma_GTP
FROM 
    smoking_data
GROUP BY 
    DRK_YN;
""")

alcohol_consumption.write.jdbc(url=url, table="alcohol_consumption", mode=mode, properties=properties)

heart_disease = spark.sql("""
SELECT
  SMK_stat_type_cd,
  heart_disease,
  age_group,
  (100 * people) / SUM(people) OVER (PARTITION BY CAST(SMK_stat_type_cd AS STRING), heart_disease) as prct
FROM (
  SELECT
    SMK_stat_type_cd,
    CASE
      WHEN tot_chole >= 240 THEN 'High Risk For Heart Disease'
      WHEN tot_chole BETWEEN 200 AND 239 THEN 'Borderline High'
      ELSE 'Low Risk For Heart Disease'
    END as heart_disease,
    CASE
      WHEN age BETWEEN 20 AND 35 THEN 'young adults'
      WHEN age BETWEEN 36 AND 50 THEN 'adults'
      WHEN age BETWEEN 51 AND 70 THEN 'middle age adults'
      ELSE 'senior adults'
    END as age_group,
    COUNT(*) as people
  FROM smoking_data
  GROUP BY SMK_stat_type_cd,
           CASE
             WHEN tot_chole >= 240 THEN 'High Risk For Heart Disease'
             WHEN tot_chole BETWEEN 200 AND 239 THEN 'Borderline High'
             ELSE 'Low Risk For Heart Disease'
           END,
           CASE
             WHEN age BETWEEN 20 AND 35 THEN 'young adults'
             WHEN age BETWEEN 36 AND 50 THEN 'adults'
             WHEN age BETWEEN 51 AND 70 THEN 'middle age adults'
             ELSE 'senior adults'
           END
) as subquery
WHERE age_group != 'senior adults' AND heart_disease = 'High Risk For Heart Disease'
ORDER BY SMK_stat_type_cd, heart_disease, age_group;
""")

heart_disease.write.jdbc(url=url, table="heart_disease", mode=mode, properties=properties)

bmi_vs_smoke_2 = spark.sql("""
SELECT
  SMK_stat_type_cd,
  CASE 
    WHEN (weight / POWER(height/100, 2)) < 18.5 THEN 'Underweight'
    WHEN (weight / POWER(height/100, 2)) BETWEEN 18.5 AND 24.9 THEN 'Normal'
    WHEN (weight / POWER(height/100, 2)) BETWEEN 25 AND 29.9 THEN 'Overweight'
    ELSE 'Obese'
  END AS BMI_category,
  count(*)
FROM smoking_data
GROUP BY SMK_stat_type_cd,
         CASE 
           WHEN (weight / POWER(height/100, 2)) < 18.5 THEN 'Underweight'
           WHEN (weight / POWER(height/100, 2)) BETWEEN 18.5 AND 24.9 THEN 'Normal'
           WHEN (weight / POWER(height/100, 2)) BETWEEN 25 AND 29.9 THEN 'Overweight'
           ELSE 'Obese'
         END;
""")

bmi_vs_smoke_2.write.jdbc(url=url, table="bmi_vs_smoke_2", mode=mode, properties=properties)