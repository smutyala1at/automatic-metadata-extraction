import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gridspec
from scipy import stats
import seaborn as sns
import os


# Training loss values
training_steps = list(range(1, 78))
training_loss = [
    1.648700, 1.506100, 1.567500, 1.003200, 1.284700, 1.609900, 1.235000, 1.412500, 1.533700, 1.247500, 
    1.159600, 1.281100, 1.200200, 1.152900, 1.177400, 1.091800, 0.855200, 0.966900, 1.303400, 1.417100, 
    1.940600, 1.295800, 1.302000, 1.540600, 1.180900, 1.121100, 1.211000, 0.929800, 1.282300, 1.465300, 
    1.072800, 1.274800, 1.011500, 1.299600, 1.230100, 1.171400, 0.995700, 0.800800, 1.093600, 1.147300, 
    1.012400, 1.277900, 1.108400, 1.269100, 1.160900, 1.259300, 1.278000, 1.260300, 0.975000, 1.409300, 
    1.286200, 0.974400, 1.052700, 1.576800, 0.916500, 1.110300, 1.285000, 1.138300, 1.246900, 1.136400, 
    1.156100, 1.023500, 1.076700, 1.413000, 1.085800, 0.954400, 1.066000, 1.008800, 1.154800, 1.061300, 
    1.244500, 1.262500, 1.129500, 1.412300, 0.860700, 1.075800, 1.536700
]

# Set consistent style for all plots
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18,
    'figure.figsize': (12, 8),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Calculate key statistics used across plots
mean_loss = np.mean(training_loss)
min_loss = min(training_loss)
min_loss_idx = training_loss.index(min_loss)
max_loss = max(training_loss)
max_loss_idx = training_loss.index(max_loss)

# Calculate first half vs second half improvement
half_idx = len(training_loss) // 2
first_half_mean = np.mean(training_loss[:half_idx])
second_half_mean = np.mean(training_loss[half_idx:])
improvement = (first_half_mean - second_half_mean) / first_half_mean * 100

# Create result folder if it doesn't exist
if not os.path.exists('result'):
    os.makedirs('result')
    print("Created 'result' directory for saving visualizations.")
print("Generating all visualizations...")

# 0. SIMPLIFIED CONVERGENCE VISUALIZATION WITH SINGLE KEY METRIC
fig, ax1 = plt.subplots(figsize=(12, 7))

# Calculate rolling standard deviation (THE key convergence metric)
window_size = 10
convergence_metric = []

for i in range(len(training_loss)):
    if i < window_size:
        window_data = training_loss[:i+1]
    else:
        window_data = training_loss[i-window_size+1:i+1]
    std_dev = np.std(window_data)
    convergence_metric.append(std_dev)

# Plot loss values as background in light color
ax1.plot(training_steps, training_loss, 'o-', color='#1f77b4', alpha=0.2, 
         markersize=3, label='Training Loss')

# Plot convergence metric prominently
ax1.plot(training_steps, convergence_metric, 'r-', linewidth=3, 
         label=f'Convergence Metric (Rolling StdDev, window={window_size})')

# Highlight minimum training loss (optional clarity)
min_idx = np.argmin(training_loss)
min_step = training_steps[min_idx]
min_loss = training_loss[min_idx]
ax1.plot(min_step, min_loss, 'ko', markersize=6)
ax1.annotate(f"Min Loss: {min_loss:.2f}", 
             xy=(min_step, min_loss), 
             xytext=(min_step + 5, min_loss + 0.1),
             arrowprops=dict(arrowstyle='->', lw=1.2),
             fontsize=12)

# Calculate improvement percentage
start_std = np.mean(convergence_metric[:15])
end_std = np.mean(convergence_metric[-15:])
std_improvement = (start_std - end_std) / start_std * 100

# Add annotation near the convergence metric area (bottom-left)
plt.annotate(f"Convergence Improvement: {std_improvement:.1f}%", 
             xy=(0.39, 0.02), xycoords='axes fraction', ha='left', va='bottom',
             fontsize=13, bbox=dict(facecolor='white', alpha=0.9, boxstyle='round'))



# Labels and formatting
plt.title('Training Convergence Analysis', fontsize=16)
plt.xlabel('Training Steps', fontsize=14)
plt.ylabel('Loss / Std. Deviation', fontsize=14)
plt.grid(True, alpha=0.3)

# Place legend cleanly below the plot
plt.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=2, fontsize=12)

# Ensure integer x-axis ticks
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

# Layout and saving
plt.tight_layout()
plt.savefig('result/essential_convergence.pdf', bbox_inches='tight')
plt.savefig('result/essential_convergence.png', dpi=300, bbox_inches='tight')
plt.close()
print("0. Essential convergence visualization saved.")

# 1. TRAINING LOSS CURVE WITH IMPROVED IMPROVEMENT ANNOTATION
fig = plt.figure(figsize=(12, 7))

# Plot the raw training loss with smaller markers to reduce visual noise
plt.plot(training_steps, training_loss, marker='o', linestyle='-', color='#1f77b4', alpha=0.6, 
         markersize=3, label='Training Loss')

# Add a smoothed trend line using moving average with optimized window size
window_size = 5 
smoothed_loss = pd.Series(training_loss).rolling(window=window_size, center=True).mean()
plt.plot(training_steps, smoothed_loss, color='#d62728', linewidth=2.5, 
         label=f'Moving Average (window={window_size})')

# Calculate linear regression line to show overall trend
x = np.array(training_steps)
y = np.array(training_loss)
m, b = np.polyfit(x, y, 1)
plt.plot(x, m*x + b, color='#2ca02c', linestyle='--', linewidth=2,
         label=f'Trend Line (slope={m:.6f})')

# Add reference line for mean
plt.axhline(y=mean_loss, color='#ff7f0e', linestyle=':', linewidth=1.5, 
            label=f'Mean Loss: {mean_loss:.4f}')

# Add titles and labels with improved spacing
plt.title('Training Loss During Fine-tuning of LLaMA 3.1 8B Model', pad=15)
plt.xlabel('Training Steps', labelpad=10)
plt.ylabel('Loss', labelpad=10)
plt.grid(True, alpha=0.3, linestyle='--')

# Improve legend positioning and style to avoid overlap
plt.legend(loc='upper right', framealpha=0.9, edgecolor='gray')

# Add annotations for min loss with improved positioning to avoid overlap
plt.annotate(f'Min Loss: {min_loss:.4f}', 
             xy=(training_steps[min_loss_idx], min_loss),
             xytext=(training_steps[min_loss_idx]-5, min_loss-0.15),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=7),
             fontsize=11, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# Add annotations for max loss
plt.annotate(f'Max Loss: {max_loss:.4f}', 
             xy=(training_steps[max_loss_idx], max_loss),
             xytext=(training_steps[max_loss_idx]+10, max_loss),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=7),
             fontsize=11, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# Plot a vertical line at the halfway point with improved visibility
midpoint = training_steps[half_idx]
plt.axvline(x=midpoint, color='#ff7f0e', linestyle='--', alpha=0.5, linewidth=1.5)

# Calculate buffer for padding
buffer = (max_loss - min_loss) * 0.15

# Create a proper annotation for the improvement percentage
plt.annotate(f'Improvement: {improvement:.2f}%\n(1st half to 2nd half)', 
             xy=(midpoint, mean_loss), 
             xytext=(midpoint, mean_loss + 0.25), 
             ha='center', 
             fontsize=11, 
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# Draw a horizontal line showing average of first half
first_half_steps = training_steps[:half_idx]
plt.plot([first_half_steps[0], first_half_steps[-1]], 
         [first_half_mean, first_half_mean], 
         'k-', alpha=0.3, linewidth=2)

# Draw a horizontal line showing average of second half
second_half_steps = training_steps[half_idx:]
plt.plot([second_half_steps[0], second_half_steps[-1]], 
         [second_half_mean, second_half_mean], 
         'k-', alpha=0.3, linewidth=2)

# Add a curved arrow connecting the two halves to illustrate the improvement
arrow_props = dict(arrowstyle='<->', color='#ff7f0e', 
                  connectionstyle="arc3,rad=0.3", 
                  linewidth=2)

plt.annotate('', 
             xy=(np.mean(first_half_steps), first_half_mean), 
             xytext=(np.mean(second_half_steps), second_half_mean),
             arrowprops=arrow_props)

# Add y-axis limits with appropriate padding
plt.ylim(min_loss - buffer, max_loss + buffer)

# Ensure x-axis has integer ticks for steps
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

plt.tight_layout()
plt.savefig('result/llm_training_loss.pdf', bbox_inches='tight')
plt.savefig('result/llm_training_loss.png', dpi=300, bbox_inches='tight')
plt.close()
print("1. Training loss curve saved.")


# 2. CONVERGENCE ANALYSIS WITH IMPROVED VISUALIZATION
plt.figure(figsize=(12, 7))

# Define training phases
phase_size = len(training_loss) // 3
early_phase = training_loss[:phase_size]
middle_phase = training_loss[phase_size:2*phase_size]
late_phase = training_loss[2*phase_size:]

# Calculate detailed statistics for each phase
phases = ['Early Phase\n(Steps 1-25)', 'Middle Phase\n(Steps 26-51)', 'Late Phase\n(Steps 52-77)']
means = [np.mean(early_phase), np.mean(middle_phase), np.mean(late_phase)]
medians = [np.median(early_phase), np.median(middle_phase), np.median(late_phase)]
stds = [np.std(early_phase), np.std(middle_phase), np.std(late_phase)]
mins = [min(early_phase), min(middle_phase), min(late_phase)]
maxs = [max(early_phase), max(middle_phase), max(late_phase)]
iqrs = [np.percentile(early_phase, 75) - np.percentile(early_phase, 25),
        np.percentile(middle_phase, 75) - np.percentile(middle_phase, 25),
        np.percentile(late_phase, 75) - np.percentile(late_phase, 25)]

# Create bar plot with error bars
colors = ['#4c72b0', '#dd8452', '#55a868']
plt.bar(phases, means, yerr=stds, alpha=0.7, capsize=7, color=colors, width=0.6)


for i, (m, s, med, min_val, max_val) in enumerate(zip(means, stds, medians, mins, maxs)):
    plt.annotate(f'μ = {m:.3f}', xy=(i, m - 0.06), ha='center', va='center', fontsize=11, 
                 fontweight='bold', color='white', bbox=dict(facecolor='none', edgecolor='none'))
    
    plt.annotate(f'σ = {s:.3f}', xy=(i, m + s + 0.08), ha='center', fontsize=10)
    
    plt.annotate(f'med = {med:.3f}', xy=(i, m - 0.20), ha='center', fontsize=10,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

# Calculate and show convergence metrics
variance_reduction = (stds[0] - stds[2]) / stds[0] * 100
stabilization = (1 - (stds[2] / stds[0])) * 100
mean_improvement = (means[0] - means[2]) / means[0] * 100

plt.title('Training Convergence Analysis by Phase', pad=15)
plt.ylabel('Mean Loss', labelpad=10)
plt.grid(axis='y', alpha=0.3, linestyle='--')


max_y = max([m + s for m, s in zip(means, stds)]) + 0.3  
min_y = min([min(means) - 0.3, 0.95])  
plt.ylim(min_y, max_y)

plt.figtext(0.5, 0.02, 
            f"Variance Reduction: {variance_reduction:.1f}% | Loss Stability Improvement: {stabilization:.1f}% | Mean Loss Improvement: {mean_improvement:.1f}%", 
            ha="center", fontsize=11, 
            bbox={"facecolor":"#f0f0f0", 
                  "edgecolor":"gray", 
                  "alpha":0.9, 
                  "pad":8, 
                  "boxstyle":"round,pad=0.8"})

plt.tight_layout(rect=[0, 0.07, 1, 0.95]) 

plt.savefig('result/training_convergence.pdf', bbox_inches='tight')
plt.savefig('result/training_convergence.png', dpi=300, bbox_inches='tight')
plt.close()
print("2. Convergence analysis saved.")


# 3. LOSS DISTRIBUTION ANALYSIS
plt.figure(figsize=(12, 7))

# Create a histogram of loss values with KDE
sns_colors = ['#3274A1', '#E1812C', '#3A923A', '#C03D3E', '#9372B2']
bins = np.linspace(min(training_loss) - 0.05, max(training_loss) + 0.05, 15)

# Main histogram
plt.hist(training_loss, bins=bins, alpha=0.7, color=sns_colors[0], 
         edgecolor='black', linewidth=1.2, density=True, label='Loss Distribution')

# Add KDE curve
from scipy.stats import gaussian_kde
kde = gaussian_kde(training_loss)
x_range = np.linspace(min(training_loss) - 0.1, max(training_loss) + 0.1, 1000)
plt.plot(x_range, kde(x_range), color=sns_colors[3], linewidth=2.5, label='Density Estimation')

# Add reference lines for statistics
plt.axvline(mean_loss, color=sns_colors[1], linestyle='--', linewidth=2.0, 
           label=f'Mean: {mean_loss:.4f}')
plt.axvline(np.median(training_loss), color=sns_colors[2], linestyle=':', linewidth=2.0, 
           label=f'Median: {np.median(training_loss):.4f}')

# Calculate percentiles for reference
p25 = np.percentile(training_loss, 25)
p75 = np.percentile(training_loss, 75)

# Highlight the interquartile range
plt.axvspan(p25, p75, alpha=0.2, color=sns_colors[4], 
            label=f'IQR: {p75-p25:.4f} (25-75th percentile)')

# Calculate key distribution statistics
skewness = stats.skew(training_loss)
kurtosis = stats.kurtosis(training_loss)

# Add titles and labels
plt.title('Distribution of Training Loss Values', pad=15)
plt.xlabel('Loss Value', labelpad=10)
plt.ylabel('Density', labelpad=10)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right', framealpha=0.9, edgecolor='gray')

# Add distribution statistics as text
stats_text = (f"Distribution Statistics:\n"
              f"Range: [{min_loss:.4f}, {max_loss:.4f}]\n"
              f"Standard Deviation: {np.std(training_loss):.4f}\n"
              f"Skewness: {skewness:.4f}\n"
              f"Kurtosis: {kurtosis:.4f}")
plt.annotate(stats_text, xy=(0.05, 0.95), xycoords='axes fraction',
             va='top', ha='left', fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8))

plt.tight_layout()
plt.savefig('result/loss_distribution.pdf', bbox_inches='tight')
plt.savefig('result/loss_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("3. Loss distribution analysis saved.")


# QUARTILE ANALYSIS - SEPARATED PLOTS

# Setup quartile data
quartile_size = len(training_loss) // 4
q1_data = training_loss[:quartile_size]
q2_data = training_loss[quartile_size:2*quartile_size]
q3_data = training_loss[2*quartile_size:3*quartile_size]
q4_data = training_loss[3*quartile_size:]

quartiles = [q1_data, q2_data, q3_data, q4_data]
quartile_names = ['First Quartile\n(Steps 1-19)', 'Second Quartile\n(Steps 20-38)', 
                  'Third Quartile\n(Steps 39-57)', 'Fourth Quartile\n(Steps 58-77)']

# Calculate statistics for each quartile
q_means = [np.mean(q) for q in quartiles]
q_stds = [np.std(q) for q in quartiles]
q_mins = [min(q) for q in quartiles]
q_maxs = [max(q) for q in quartiles]
q_medians = [np.median(q) for q in quartiles]
q_ranges = [max(q) - min(q) for q in quartiles]
q_cvs = [np.std(q) / np.mean(q) for q in quartiles]

# Calculate convergence metrics
q1_to_q4_std_change = (q_stds[0] - q_stds[3]) / q_stds[0] * 100
q1_to_q4_mean_change = (q_means[0] - q_means[3]) / q_means[0] * 100

# 4. PLOT 1: Quartile Means with Standard Deviation
plt.figure(figsize=(12, 7))

# Create bars with error bars
bars = plt.bar(quartile_names, q_means, yerr=q_stds, capsize=7, alpha=0.7, 
        color=['#4c72b0', '#55a868', '#c44e52', '#8172b3'])
plt.title('Quartile Means with Standard Deviation', pad=15)
plt.ylabel('Loss Value', labelpad=10)
plt.tick_params(axis='x', rotation=0)
plt.grid(axis='y', alpha=0.3, linestyle='--')

# Add mean values and std as text below the bars to avoid overlap
for i, (m, s) in enumerate(zip(q_means, q_stds)):
    plt.text(i, 0.8, f'{m:.3f}±{s:.3f}', ha='center', fontsize=11, 
             fontweight='bold', color='black')

# Set y-axis limits to ensure text is visible
plt.ylim(0, max(q_means) + max(q_stds) + 0.1)

plt.tight_layout()
plt.savefig('result/quartile_means.pdf', bbox_inches='tight')
plt.savefig('result/quartile_means.png', dpi=300, bbox_inches='tight')
plt.close()
print("4. Improved quartile means plot saved with no text overlap.")

# 5. PLOT 2: Variability Metrics by Quartile
plt.figure(figsize=(12, 7))
x = range(len(quartile_names))
plt.plot(x, q_ranges, 'o-', markersize=8, linewidth=2, label='Range', color='#c44e52')
plt.plot(x, q_stds, 's-', markersize=8, linewidth=2, label='Std Dev', color='#4c72b0')
plt.title('Variability Metrics by Quartile', pad=15)
plt.xticks(x, ['Q1', 'Q2', 'Q3', 'Q4'])
plt.ylabel('Value', labelpad=10)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='best')

# Add coefficient of variation as text
for i, cv in enumerate(q_cvs):
    plt.annotate(f'CV: {cv:.3f}', xy=(i, q_ranges[i] + 0.05), ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('result/variability_metrics.pdf', bbox_inches='tight')
plt.savefig('result/variability_metrics.png', dpi=300, bbox_inches='tight')
plt.close()
print("5. Variability metrics plot saved.")

# 6. PLOT 3: Loss Distribution by Quartile (Boxplot)
plt.figure(figsize=(12, 10))

# Create the boxplot with customized appearance
box = plt.boxplot([q1_data, q2_data, q3_data, q4_data], 
                  patch_artist=True, 
                  tick_labels=['Q1', 'Q2', 'Q3', 'Q4'],
                  widths=0.6)

# Customize boxplot colors
box_colors = ['#4c72b0', '#55a868', '#c44e52', '#8172b3']
for patch, color in zip(box['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Label the median lines more explicitly
for i, (median_line, q_name) in enumerate(zip(box['medians'], ['Q1', 'Q2', 'Q3', 'Q4'])):
    median_value = np.median([q1_data, q2_data, q3_data, q4_data][i])
    plt.annotate(f'Median: {median_value:.3f}', 
                xy=(i+1, median_value),
                xytext=(i+1, median_value - 0.13),
                ha='center', 
                fontsize=9,
                arrowprops=dict(arrowstyle='->', color='black', lw=1),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# Add text showing convergence
convergence_text = (f"Q1→Q4 Changes:\nStd Dev: {q1_to_q4_std_change:.1f}%\n"
                    f"Mean: {q1_to_q4_mean_change:.1f}%")
plt.annotate(convergence_text, xy=(0.05, 0.95), xycoords='axes fraction',
             va='top', fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8))

# Title and axis labels
plt.title('Loss Distribution by Quartile', pad=15)
plt.ylabel('Loss Value', labelpad=10)
plt.grid(axis='y', alpha=0.3, linestyle='--')

# First apply tight_layout to ensure the main plot is properly sized
plt.tight_layout()

# Then create a new figure for the boxplot guide
fig_guide = plt.figure(figsize=(12, 3))
ax_guide = fig_guide.add_subplot(111)

# Create a simple boxplot in the guide figure
demo_data = [[0.8, 1.0, 1.2, 1.5, 1.8, 2.0]]
demo_box = ax_guide.boxplot(demo_data, patch_artist=True, widths=0.4)
demo_box['boxes'][0].set_facecolor('lightgray')
demo_box['boxes'][0].set_alpha(0.7)
ax_guide.set_xticklabels([])
ax_guide.set_title("BOXPLOT GUIDE: Understanding the Elements", fontsize=12)

# Add annotations to each part of the boxplot
ax_guide.annotate("Maximum\n(excluding outliers)", 
                 xy=(1, demo_data[0][-2]), xytext=(1.3, demo_data[0][-2]),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

ax_guide.annotate("75th Percentile\n(Upper Quartile)", 
                 xy=(1, np.percentile(demo_data[0], 75)), xytext=(1.3, np.percentile(demo_data[0], 75)),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

ax_guide.annotate("Median", 
                 xy=(1, np.median(demo_data[0])), xytext=(1.3, np.median(demo_data[0])),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

ax_guide.annotate("25th Percentile\n(Lower Quartile)", 
                 xy=(1, np.percentile(demo_data[0], 25)), xytext=(1.3, np.percentile(demo_data[0], 25)),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

ax_guide.annotate("Minimum\n(excluding outliers)", 
                 xy=(1, demo_data[0][0]), xytext=(1.3, demo_data[0][0]),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

# Add text about outliers
ax_guide.annotate("Outliers: Points beyond\n1.5× IQR from box", 
                 xy=(1, 2.0), xytext=(1.3, 2.0),
                 ha="left", fontsize=9, va="center",
                 arrowprops=dict(arrowstyle="->", color='black', lw=0.8))

# Add a note about IQR (Interquartile Range)
ax_guide.text(0.5, 0.05, 
             "IQR (Interquartile Range): The box shows the middle 50% of data from the 25th to 75th percentile.\nNote: The mean is NOT shown in a standard boxplot, only the median.",
             ha="center", fontsize=10, transform=ax_guide.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.8))

# Adjust the guide axis limits
ax_guide.set_ylim(0.5, 2.1)
ax_guide.set_xlim(0.5, 2.5)
ax_guide.grid(False)

# Save the guide figure separately
plt.tight_layout()
fig_guide.savefig('result/boxplot_guide.png', dpi=300, bbox_inches='tight')
plt.close(fig_guide)

# go back to the main figure and save it
plt.figure(1) 
plt.savefig('result/loss_distribution_boxplot.pdf', bbox_inches='tight')
plt.savefig('result/loss_distribution_boxplot.png', dpi=300, bbox_inches='tight')
plt.close()

print("6. Improved loss distribution boxplot saved with clear explanations for non-statisticians.")
print("   Also created a separate boxplot guide image for easier layout management.")

# 7. PLOT 4: Quartile Trends with Regression Lines
plt.figure(figsize=(12, 7))
markers = ['o', 's', '^', 'd']
colors = ['#4c72b0', '#55a868', '#c44e52', '#8172b3']

text_positions = [
    {'x': 3, 'y': 1.5041},    
    {'x': 21, 'y': 1.4952},   
    {'x': 38, 'y': 1.2},       
    {'x': 58, 'y': 1.07}      
]

for i, (quartile, name, marker, color) in enumerate(zip(quartiles, 
                                                       ['Q1', 'Q2', 'Q3', 'Q4'],
                                                       markers, colors)):
    # Create x-values that represent the actual training steps for this quartile
    start_idx = i * quartile_size
    x_vals = np.array(training_steps[start_idx:start_idx + len(quartile)])
    y_vals = np.array(quartile)
    
    # Plot the scatter points
    plt.scatter(x_vals, y_vals, marker=marker, color=color, s=35, alpha=0.7, label=name)
    
    # Calculate and plot regression line
    if len(x_vals) > 1: 
        m, b = np.polyfit(x_vals, y_vals, 1)
        plt.plot(x_vals, m*x_vals + b, '--', color=color, linewidth=1.5)
        
        plt.annotate(f'{name} slope: {m:.4f}', 
                     xy=(text_positions[i]['x'], text_positions[i]['y']),
                     fontsize=9, color=color,
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, alpha=0.8))

plt.title('Quartile Trends with Regression Lines', pad=15)
plt.xlabel('Training Steps', labelpad=10)
plt.ylabel('Loss Value', labelpad=10)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right')

plt.tight_layout()
plt.savefig('result/quartile_trends.pdf', bbox_inches='tight')
plt.savefig('result/quartile_trends.png', dpi=300, bbox_inches='tight')
plt.close()
print("7. Quartile trends plot saved.")

# Final summary of all key metrics saved to file
with open('training_analysis_summary.txt', 'w') as f:
    f.write("TRAINING LOSS ANALYSIS SUMMARY\n")
    f.write("==========================\n\n")
    
    f.write("OVERALL STATISTICS:\n")
    f.write(f"Total Training Steps: {len(training_loss)}\n")
    f.write(f"Mean Loss: {mean_loss:.4f}\n")
    f.write(f"Median Loss: {np.median(training_loss):.4f}\n")
    f.write(f"Minimum Loss: {min_loss:.4f} (at step {min_loss_idx + 1})\n")
    f.write(f"Maximum Loss: {max_loss:.4f} (at step {max_loss_idx + 1})\n")
    f.write(f"Standard Deviation: {np.std(training_loss):.4f}\n")
    f.write(f"Coefficient of Variation: {np.std(training_loss)/mean_loss:.4f}\n")
    f.write(f"Linear Trend Slope: {m:.6f}\n\n")
    
    f.write("KEY CONVERGENCE METRIC:\n")
    f.write(f"Rolling Standard Deviation Improvement: {std_improvement:.2f}%\n\n")
    
    f.write("HALF ANALYSIS:\n")
    f.write(f"First Half Mean: {first_half_mean:.4f}\n")
    f.write(f"Second Half Mean: {second_half_mean:.4f}\n")
    f.write(f"Improvement: {improvement:.2f}%\n\n")
    
    f.write("PHASE ANALYSIS:\n")
    for i, phase in enumerate(phases):
        f.write(f"{phase}:\n")
        f.write(f"  Mean: {means[i]:.4f}\n")
        f.write(f"  Median: {medians[i]:.4f}\n")
        f.write(f"  Std Dev: {stds[i]:.4f}\n")
        f.write(f"  Min/Max: {mins[i]:.4f}/{maxs[i]:.4f}\n")
        f.write(f"  Range: {maxs[i] - mins[i]:.4f}\n")
        f.write(f"  IQR: {iqrs[i]:.4f}\n\n")
    
    f.write("QUARTILE ANALYSIS:\n")
    for i, qname in enumerate(quartile_names):
        f.write(f"{qname}:\n")
        f.write(f"  Mean: {q_means[i]:.4f}\n")
        f.write(f"  Std Dev: {q_stds[i]:.4f}\n")
        f.write(f"  Range: {q_ranges[i]:.4f}\n")
        f.write(f"  Coef of Variation: {q_cvs[i]:.4f}\n\n")
    
    f.write("CONVERGENCE METRICS:\n")
    f.write(f"Variance Reduction (Early to Late): {variance_reduction:.2f}%\n")
    f.write(f"Stability Improvement: {stabilization:.2f}%\n")
    f.write(f"Mean Loss Improvement (Early to Late): {mean_improvement:.2f}%\n")
    f.write(f"Q1 to Q4 Std Dev Change: {q1_to_q4_std_change:.2f}%\n")
    f.write(f"Q1 to Q4 Mean Change: {q1_to_q4_mean_change:.2f}%\n")
    f.write(f"Step-by-Step Analysis: Start to End Std Dev Improvement: {std_improvement:.2f}%\n")

print("Analysis complete. All visualizations and summary have been saved.")