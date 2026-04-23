import matplotlib.pyplot as plt
import csv

file_sizes = []
latencies = []
throughputs = []

with open("performance.csv", "r") as f:
    reader = csv.DictReader(f)

    for row in reader:
        size = int(row["file_size"])
        time_taken = float(row["duration_seconds"])

        file_sizes.append(size)
        latencies.append(time_taken)

        if time_taken > 0:
            throughputs.append(size / time_taken)

# 📈 Line Graph
plt.figure(figsize=(8, 5))
plt.plot(file_sizes, latencies, marker='o', color='blue', linewidth=2)
plt.xlabel("File Size (bytes)")
plt.ylabel("Latency (seconds)")
plt.title("Latency vs File Size")
plt.grid(True)

plt.tight_layout()
plt.savefig("latency_line_graph.png")
print("✅ Saved: latency_line_graph.png")

plt.close()

# 📊 Histogram
plt.figure(figsize=(8, 5))
plt.hist(throughputs, bins=6, color='green', edgecolor='black')
plt.xlabel("Throughput (bytes/sec)")
plt.ylabel("Frequency")
plt.title("Throughput Distribution Histogram")

plt.tight_layout()
plt.savefig("throughput_histogram.png")
print("✅ Saved: throughput_histogram.png")

plt.close()