# 📊 Database Performance Benchmarking across SQL and NoSQL Database Systems

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge)
![Cassandra](https://img.shields.io/badge/Cassandra-1287B1?style=for-the-badge)
![Benchmarking](https://img.shields.io/badge/Performance-Benchmarking-success?style=for-the-badge)
![MIT](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

---

# 📖 Overview

This project presents a comprehensive performance benchmarking study of five widely used database management systems:

- MySQL (Relational)
- MongoDB (Document)
- Cassandra (Wide-column)
- Redis (Key-Value)
- Neo4j (Graph)

A synthetic Course Management System dataset containing **1 million records** was generated using Python's Faker library and deployed across Dockerized database environments. Each database was benchmarked under identical workloads using standardized queries and varying dataset sizes to evaluate scalability, execution time, and overall performance.

The project demonstrates practical applications of database engineering, Docker containerization, benchmarking methodologies, and Python automation for large-scale data processing.

---

# 🎯 Objectives

- Compare SQL and NoSQL database performance.
- Benchmark query execution across different database paradigms.
- Analyze scalability using datasets ranging from **250K to 1 Million records**.
- Measure both cold-start and average query execution times.
- Evaluate database suitability for different application workloads.

---

# 🏗️ Technologies Used

| Category | Technologies |
|-----------|--------------|
| Programming Language | Python |
| Containerization | Docker, Docker Compose |
| Relational Database | MySQL |
| Document Database | MongoDB |
| Graph Database | Neo4j |
| Key-Value Store | Redis |
| Wide-Column Database | Cassandra |
| Dataset Generation | Faker |
| Data Analysis | Pandas, NumPy |
| Result Visualization | Excel |

---

# 📊 Databases Compared

| Database | Type | Primary Strength |
|-----------|------|------------------|
| MySQL | Relational | ACID transactions & SQL |
| MongoDB | Document | Flexible schema |
| Cassandra | Wide-column | High scalability |
| Redis | In-memory Key-Value | Ultra-fast access |
| Neo4j | Graph | Relationship traversal |

---

# 🔄 Benchmark Workflow

```mermaid
flowchart TD

A[Generate Synthetic Dataset]
B[Dockerized Database Deployment]
C[Load Dataset]
D[Execute Benchmark Queries]
E[Measure First Execution Time]
F[Measure Average Execution Time]
G[Store Results]
H[Performance Analysis]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
G --> H
