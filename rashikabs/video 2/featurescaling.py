import matplotlib.pyplot as plt

# Data
area = [800, 1200, 2000, 1500, 950]
beds = [2, 3, 4, 3, 2]

# ---- BEFORE SCALING ----
plt.figure(figsize=(8, 6))
plt.scatter(area, beds, s=100, color='#4A9EFF', alpha=0.7)
plt.xlabel("Area (sq ft)", fontsize=12)
plt.ylabel("Number of Bedrooms", fontsize=12)
plt.title("Before Scaling: Area Dominates", fontsize=14)
plt.grid(True, alpha=0.3)

# Add labels to points
for i, (a, b) in enumerate(zip(area, beds)):
    plt.annotate(f"House {i+1}", (a, b), xytext=(5, 5), textcoords='offset points', fontsize=9)

plt.savefig("scaling_before.png", dpi=150, bbox_inches='tight')
plt.close()

# ---- AFTER SCALING (Normalization) ----
area_min, area_max = min(area), max(area)
beds_min, beds_max = min(beds), max(beds)

area_norm = [(x - area_min) / (area_max - area_min) for x in area]
beds_norm = [(y - beds_min) / (beds_max - beds_min) for y in beds]

plt.figure(figsize=(8, 6))
plt.scatter(area_norm, beds_norm, s=100, color='#4A9EFF', alpha=0.7)
plt.xlabel("Area (normalized)", fontsize=12)
plt.ylabel("Bedrooms (normalized)", fontsize=12)
plt.title("After Scaling: Both Features Contribute", fontsize=14)
plt.grid(True, alpha=0.3)

# Add labels
for i, (a, b) in enumerate(zip(area_norm, beds_norm)):
    plt.annotate(f"House {i+1}", (a, b), xytext=(5, 5), textcoords='offset points', fontsize=9)

plt.savefig("scaling_after.png", dpi=150, bbox_inches='tight')
plt.close()

print("✓ Images saved successfully!")
print("  - scaling_before.png")
print("  - scaling_after.png")