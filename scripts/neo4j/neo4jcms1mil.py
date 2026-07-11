from neo4j import GraphDatabase
import pandas as pd
import time
import os
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configuration
config = {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "dbpasscms",
    "DATASET_PATH": "1_mil_records.csv",
    "OUTPUT_DIR": "/app/output",
    "NUM_EXPERIMENTS": 31,
    "BATCH_SIZE": 10000,
    "DATASET_SIZES": [250000, 500000, 750000, 1000000],
    "QUERY_TIMEOUT": 120
}

class Neo4jCMSBenchmark:
    # Function to initialize the Neo4j Connection
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_lifetime=3600,
            connection_acquisition_timeout=300,
            encrypted=False,
        )
        print("Neo4j driver initialized")

    # Function to stop the Neo4j Connection
    def close(self):
        self.driver.close()
        print("Neo4j connection closed")

    # Function to create the schema (constraints and index)
    def create_schema(self):
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.student_id IS UNIQUE",
                "CREATE CONSTRAINT professor_id IF NOT EXISTS FOR (p:Professor) REQUIRE p.professor_id IS UNIQUE",
                "CREATE CONSTRAINT assignment_id IF NOT EXISTS FOR (a:Assignment) REQUIRE a.assignment_id IS UNIQUE",
                "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.course_id IS UNIQUE",
                "CREATE INDEX course_name_index IF NOT EXISTS FOR (c:Course) ON (c.course_name)",
                "CREATE INDEX submission_status_index IF NOT EXISTS FOR (a:Assignment) ON (a.submission_status)"
            ]
            for constraint in constraints:
                session.run(constraint)
        print("Schema constraints and indexes created")

    # Function to drop the data from the database
    def drop_data(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("Database cleaned up")

    # Function to load the data in batches
    def load_data_in_batches(self, file_path, size):
        for chunk in pd.read_csv(file_path, chunksize=config["BATCH_SIZE"]):
            if size <= 0:
                break
            yield chunk.head(min(config["BATCH_SIZE"], size))
            size -= config["BATCH_SIZE"]

    # Function to insert the data
    def insert_data(self, data_size):
        total_inserted = 0
        start_time = time.time()
        
        try:
            # Loading and sorting data
            full_data = pd.concat([
                chunk for chunk in 
                pd.read_csv(config["DATASET_PATH"], chunksize=config["BATCH_SIZE"])
            ]).head(data_size)
            
            # Sorting by key fields to minimize deadlocks
            full_data = full_data.sort_values([
                'course_id', 'professor_id', 'student_id', 'assignment_id'
            ])
            
            print(f"Full dataset ({len(full_data)} records) loaded and sorted")
            
            # Split into batches
            chunks = np.array_split(full_data, max(1, len(full_data)//config["BATCH_SIZE"]))
            
            # Sequential processing (more reliable than parallel)
            for chunk in chunks:
                records = chunk.to_dict('records')
                inserted = self.process_batch(records)
                total_inserted += inserted
                print(f"Inserted {total_inserted} of {data_size} records...")
        
        except Exception as e:
            print(f"Insertion error: {str(e)}")
            return self.insert_data_chunked(data_size)
        
        elapsed = time.time() - start_time
        print(f"Inserted {total_inserted} records in {elapsed:.2f} seconds")
        return total_inserted

    # Function to execute batch processing
    def process_batch(self, records):
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    self._execute_batch_insert, 
                    records
                )
                return len(records)
        except Exception as e:
            print(f"Batch error: {str(e)}")
            return 0

    # Function to execute batch insertion
    @staticmethod
    def _execute_batch_insert(tx, records):
        query = """
        UNWIND $records AS r
        MERGE (c:Course {course_id: r.course_id})
        SET c.course_name = r.course_name,
            c.course_content = r.course_content
        
        MERGE (p:Professor {professor_id: r.professor_id})
        SET p.professor_name = r.professor_name,
            p.professor_email_address = r.professor_email_address
        
        MERGE (s:Student {student_id: r.student_id})
        SET s.student_name = r.student_name,
            s.student_email_address = r.student_email_address
        
        MERGE (p)-[:TEACHES]->(c)
        MERGE (s)-[:ENROLLED_IN]->(c)
        
        MERGE (a:Assignment {assignment_id: r.assignment_id})
        SET a.assignment_title = r.assignment_title,
            a.submission_status = r.submission_status,
            a.score = r.score
        
        MERGE (s)-[:SUBMITTED]->(a)
        """
        tx.run(query, records=records)
        return len(records)

    # Function to run query with timeout and return execution time in milliseconds
    def run_query(self, query, params=None):
        try:
            with self.driver.session() as session:
                start = time.time()
                result = session.run(query, params or {}, timeout=config["QUERY_TIMEOUT"])
                return (time.time() - start) * 1000  # Convert to milliseconds
        except Exception as e:
            print(f"Query failed: {str(e)}")
            raise
    
    # Function to run the experiments with error handling
    def run_experiments(self, query):
        metrics = {
            "first_execution_time": None,
            "average_execution_time": None,
            "execution_count": 0
        }
        
        try:
            # First execution (cold run)
            first_run = self.run_query(query)
            metrics["first_execution_time"] = first_run
            metrics["execution_count"] = 1
            
            # Subsequent executions (warm runs)
            execution_times = []
            for _ in range(config["NUM_EXPERIMENTS"] - 1):
                try:
                    execution_times.append(self.run_query(query))
                    metrics["execution_count"] += 1
                except Exception as e:
                    print(f"Query execution failed: {str(e)}")
                    continue
            
            if execution_times:
                metrics["average_execution_time"] = np.mean(execution_times)
            
        except Exception as e:
            print(f"Initial query execution failed: {str(e)}")
        
        return metrics

    # Query Function of Neo4j 
    def get_benchmark_queries(self):
        return {
            "Query1": """
                MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {course_name: 'Data Analysis'})
                RETURN s.student_id, s.student_name
                LIMIT 10
            """,
            "Query2": """
                MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {course_name: 'Data Analysis'})
                MATCH (s)-[:SUBMITTED]->(a:Assignment {submission_status: 'Yes'})
                RETURN s.student_id, s.student_name
                LIMIT 10
            """,
            "Query3": """
                MATCH (s:Student)-[:SUBMITTED]->(a:Assignment)
                WHERE s.student_id IN [540214, 533994]
                SET a.submission_status = 'Yes', a.score = 30
                WITH s, a
                MATCH (s)-[:ENROLLED_IN]->(c:Course)
                RETURN s.student_id, s.student_name, c.course_name, a.assignment_id, a.submission_status, a.score
            """,
            "Query4": """
                MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {course_name: 'Data Analysis'})
                MATCH (s)-[:SUBMITTED]->(a:Assignment {submission_status: 'Yes'})
                WHERE a.score > 26
                RETURN s.student_id, s.student_name, c.course_name, a.submission_status, a.score
            """
        }

# Main Function
def main():
    benchmark = None
    try:
        # Initializing benchmark
        benchmark = Neo4jCMSBenchmark(
            config["NEO4J_URI"],
            config["NEO4J_USER"],
            config["NEO4J_PASSWORD"]
        )
        
        # Preparin output directory
        os.makedirs(config["OUTPUT_DIR"], exist_ok=True)
        output_file = os.path.join(
            config["OUTPUT_DIR"],
            "neo4j_query_execution_times.xlsx"
        )
        
        results = []
        
        # Creating schema (constraints and indexes)
        benchmark.create_schema()
        
        # Running benchmarks for each dataset size
        for size in config["DATASET_SIZES"]:
            print(f"\n{'='*50}\nBenchmarking with {size:,} records\n{'='*50}")
            
            # Inserting data
            inserted_count = benchmark.insert_data(size)
            if inserted_count < size:
                print(f"Only inserted {inserted_count} of {size} requested records")
                size = inserted_count
            
            # Running each query
            for query_name, query in benchmark.get_benchmark_queries().items():
                print(f"Running benchmark for: {query_name}")
                
                try:
                    metrics = benchmark.run_experiments(query)
                    results.append({
                        "Records": size,
                        "Query": query_name,
                        "First Execution Time (ms)": metrics["first_execution_time"],
                        "Average Execution Time (ms)": metrics["average_execution_time"]
                    })
                except Exception as e:
                    print(f"Error running query {query_name}: {str(e)}")
                    results.append({
                        "Records": size,
                        "Query": query_name,
                        "Error": str(e)
                    })
                    continue
            
        # Dropping the data
        benchmark.drop_data()
        
        # Save results to Excel
        results_df = pd.DataFrame(results)
        results_df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"Results saved to {output_file}")
        
    except Exception as e:
        print(f"Error in benchmark execution: {str(e)}", exc_info=True)
    finally:
        if benchmark:
            benchmark.close()

if __name__ == "__main__":
    main()
