import os
import json
import pandas as pd

# 改变工作目录到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split, to_date, datediff, month, year, dayofweek, current_date, date_format, sum, avg, max, min, count, udf
from pyspark.sql.types import StringType, IntegerType, DoubleType

# 初始化SparkSession
spark = SparkSession.builder \
    .appName("Experiment4") \
    .master("local[*]") \
    .config("spark.sql.sources.useV1SourceList", "text,json,csv") \
    .getOrCreate()

print("SparkSession initialized.")

# 实验一、通过多种数据源创建DataFrame

# 1.1 从JSON文件创建DataFrame
import json
with open("students.json", "r") as f:
    students_data = json.load(f)
df_json = spark.createDataFrame(students_data)
print("1.1 df_json:")
df_json.show()
df_json.printSchema()

# 1.2 从Python可迭代对象创建DataFrame
courses_data = [
    ("大数据技术", 4, "王教授"),
    ("机器学习", 3, "李教授"),
    ("数据挖掘", 3, "张教授")
]
df_courses = spark.createDataFrame(courses_data, ["course", "credit", "teacher"])
print("1.2 df_courses:")
df_courses.show()
df_courses.printSchema()

# 1.3 从RDD创建DataFrame
cities_data = [("北京", 2154), ("上海", 2487), ("广州", 1868), ("深圳", 1756)]
rdd_cities = spark.sparkContext.parallelize(cities_data)
df_cities = rdd_cities.toDF(["city", "population"])
print("1.3 df_cities:")
df_cities.show()

# 1.4 从本地文本文件创建DataFrame
df_scores_raw = spark.sparkContext.textFile("scores.txt")
df_scores = df_scores_raw.map(lambda line: line.split(",")).toDF(["student_id", "name", "regular_score", "exam_score"])
df_scores = df_scores.withColumn("student_id", col("student_id").cast("int"))
print("1.4 df_scores:")
df_scores.show()
df_scores.printSchema()

# 实验二、DataFrame与RDD的相互转换

# 2.1 DataFrame转RDD
rdd_from_df = df_json.rdd
first_row = rdd_from_df.first()
print("2.1 First row type:", type(first_row))
print("Access by name:", first_row["name"])
print("Access by index:", first_row[1])  # Assuming name is second column
print("Take 3:")
for row in rdd_from_df.take(3):
    print(row)

# 2.2 RDD转回DataFrame
df_restored = rdd_from_df.toDF()
print("2.2 df_restored schema:")
df_restored.printSchema()
print("Original df_json schema:")
df_json.printSchema()

# 实验三、使用orderBy实现多字段排序

# 读取employees.csv
import pandas as pd
df_employees_pd = pd.read_csv("employees.csv")
df_employees = spark.createDataFrame(df_employees_pd)
print("3.1 Employees sorted by salary asc:")
df_employees.orderBy("salary").show()
print("3.1 Employees sorted by salary desc:")
df_employees.orderBy(col("salary").desc()).show()

print("3.2 Employees sorted by department asc, salary desc:")
df_employees.orderBy(col("department").asc(), col("salary").desc()).show()
print("3.2 Employees sorted by age asc, join_date asc:")
df_employees.orderBy("age", "join_date").show()

# 实验四、处理日期类型数据

# 读取orders.csv
df_orders_pd = pd.read_csv("orders.csv")
df_orders = spark.createDataFrame(df_orders_pd)
df_orders = df_orders.withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd"))
print("4.1 df_orders schema after date conversion:")
df_orders.printSchema()

df_orders = df_orders.withColumn("order_date_fmt", date_format(col("order_date"), "yyyy年MM月dd日"))
print("4.2 df_orders with formatted date:")
df_orders.show()

df_orders = df_orders.withColumn("days_since_order", datediff(current_date(), col("order_date"))) \
                     .withColumn("order_month", month(col("order_date")))
print("4.3 df_orders with calculations:")
df_orders.show()

monthly_orders = df_orders.groupBy("order_month").count()
print("4.3 Monthly order counts:")
monthly_orders.show()

# 实验五、使用distinct消除重复行

df_visits_pd = pd.read_csv("visits.csv")
df_visits = spark.createDataFrame(df_visits_pd)
print("5.1 Original visits count:", df_visits.count())
print("5.1 Sample data:")
df_visits.show()

df_visits_distinct = df_visits.distinct()
print("5.2 Distinct visits count:", df_visits_distinct.count())
print("5.2 Distinct data:")
df_visits_distinct.show()

# 实验六、使用drop删除列

print("6.1 Original columns:", df_employees.columns)
df_employees_drop1 = df_employees.drop("join_date")
print("6.1 After dropping join_date:", df_employees_drop1.columns)

df_employees_drop2 = df_employees.drop("emp_id", "join_date")
print("6.2 After dropping emp_id and join_date:", df_employees_drop2.columns)
df_employees_drop2.show()

# 实验七、使用exceptAll进行差集运算

df_old_pd = pd.read_csv("old_records.csv")
df_old = spark.createDataFrame(df_old_pd)
df_new_pd = pd.read_csv("new_records.csv")
df_new = spark.createDataFrame(df_new_pd)
print("7.1 df_old:")
df_old.show()
print("7.1 df_new:")
df_new.show()

df_diff_old_new = df_old.exceptAll(df_new)
print("7.2 df_old.exceptAll(df_new):")
df_diff_old_new.show()

df_diff_new_old = df_new.exceptAll(df_old)
print("7.2 df_new.exceptAll(df_old):")
df_diff_new_old.show()

# 实验八、多表关联与分组聚合

df_sales_pd = pd.read_csv("sales.csv")
df_sales = spark.createDataFrame(df_sales_pd)
df_products_pd = pd.read_csv("products.csv")
df_products = spark.createDataFrame(df_products_pd)

df_joined = df_sales.join(df_products, on="product_id", how="inner") \
                    .select("sale_id", "product_name", "category", "quantity", "unit_price", "region")
print("8.1 Joined data:")
df_joined.show()

df_joined = df_joined.withColumn("total_sales", col("quantity") * col("unit_price"))
region_agg = df_joined.groupBy("region").agg(
    sum("total_sales").alias("region_total"),
    count("sale_id").alias("order_count"),
    avg("total_sales").alias("avg_order")
)
print("8.2 Region aggregation:")
region_agg.show()

region_category_agg = df_joined.groupBy("region", "category").agg(
    sum("total_sales").alias("total_sales"),
    count("sale_id").alias("order_count")
)
print("8.3 Region and category aggregation:")
region_category_agg.show()

# 实验九、UDF用户自定义函数

def salary_level(salary):
    if salary >= 17000:
        return "高级"
    elif salary >= 13000:
        return "中级"
    else:
        return "初级"

udf_salary_level = udf(salary_level, StringType())
df_employees_with_level = df_employees.withColumn("level", udf_salary_level(col("salary")))
print("9.1 Employees with level:")
df_employees_with_level.show()

df_senior = df_employees_with_level.where(col("level") == "高级").select("name", "department", "salary")
print("9.2 Senior employees:")
df_senior.show()

# 实验十、列操作与描述性统计

df_employees = df_employees.withColumn("annual_salary", col("salary") * 12) \
                           .withColumn("salary_after_tax", col("salary") * 0.8)
print("10.1 Employees with new columns:")
df_employees.show()

df_employees_renamed = df_employees.withColumnRenamed("name", "employee_name") \
                                   .withColumnRenamed("department", "dept")
print("10.2 Renamed columns:", df_employees_renamed.columns)

df_selected = df_employees.selectExpr("salary * 12 AS yearly_income", "name", "department")
print("10.3 Selected with expr:")
df_selected.show()

print("10.4 Describe all:")
df_employees.describe().show()

print("10.4 Describe salary:")
df_employees.describe("salary").show()

print("10.5 Summary salary:")
df_employees.summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "max").show()

# 收尾
spark.stop()
print("SparkSession stopped.")