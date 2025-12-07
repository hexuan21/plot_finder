import json
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os
import re
from collections import Counter
from pathlib import Path

def word_cloud(
    data
):
    summary_list=[x['summary'] for x in data]
    combined_text = " ".join(summary_list)
    text_list=combined_text.split(" ")
    new_text_list=[]
    for x in text_list:
        if len(x)>2:
            new_text_list.append(x)
    combined_text=" ".join(new_text_list)
    
    # Create and generate the word cloud
    background_color="white"
    width=1200
    height=800
    max_words=300
    wc = WordCloud(
        background_color=background_color,
        width=width,
        height=height,
        max_words=max_words,
        stopwords=None, 
        collocations=False
    ).generate(combined_text)

    plt.figure(figsize=(width/100, height/100))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/wordcloud.png")


def summ_len_hist(data, bins=40, title="Word Count Histogram"):
    summary_list=[x['summary'] for x in data]
    raw_word_counts = [len(s.split(" ")) for s in summary_list]
    word_counts = []
    for x in raw_word_counts:
        if x<=MAX_WORDS and x>=MIN_WORDS:
            word_counts.append(x)
            
    print(f"Total valid sentences: {len(word_counts)}")
    print(f"Average word count: {sum(word_counts)/len(word_counts):.2f}")
    print(f"Max words: {max(word_counts)}, Min words: {min(word_counts)}")

    plt.figure(figsize=(10, 6))
    plt.hist(word_counts, bins=bins, color="skyblue", edgecolor="black")
    plt.title(title)
    plt.xlabel("Number of words per string")
    plt.ylabel("Frequency")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    output_path=f"{PLOT_DIR}/summary_length_histogram.png"
    plt.savefig(output_path, dpi=300)


def release_year_hist(data):
    
    def extract_year(s):
        match = re.match(r"^(\d{4})", s.strip())
        if match:
            return int(match.group(1))
        return None
    
    def group_years(years):
        grouped = Counter()
        for y in years:
            base = y - (y % 5)
            label = f"{base}"
            grouped[label] += 1
        return grouped
    
    strings= [x['release_date'] for x in data]
    years = [extract_year(s) for s in strings if extract_year(s) is not None]

    if not years:
        print("No valid years found.")
        return

    grouped_counts = group_years(years)
    labels = sorted(grouped_counts.keys(), key=lambda x: int(x.split('-')[0]))
    values = [grouped_counts[l] for l in labels]
    title="Release Year Histogram"
    # 打印统计信息
    print(f"Total entries: {len(strings)}")
    print(f"Valid years: {len(years)}")
    print(f"Range: {min(years)} - {max(years)}")

    # 绘图
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color="skyblue", edgecolor="black", width=0.8)
    plt.xticks(rotation=45, ha='right')
    plt.title(title)
    plt.xlabel("5-Year Range")
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    output_path=f"{PLOT_DIR}/release_year_histogram.png"
    plt.savefig(output_path, dpi=300)
    

def run_time_hist(data):
    raw_run_times = [float(x['runtime']) for x in data if x['runtime'] not in [None, "", "N/A"]]
    run_times=[]
    for x in raw_run_times:
        if x>MIN_RUN_TIME and x<MAX_RUN_TIME:
            run_times.append(x)
            
    if not run_times:
        print("No valid runtimes found.")
        return

    print(f"Total entries: {len(data)}")
    print(f"Valid runtimes: {len(run_times)}")
    print(f"Range: {min(run_times)} - {max(run_times)}")

    plt.figure(figsize=(10, 6))
    plt.hist(run_times, bins=30, color="skyblue", edgecolor="black")
    plt.title("Runtime Histogram")
    plt.xlabel("Runtime (minutes)")
    plt.ylabel("Frequency")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    output_path=f"{PLOT_DIR}/runtime_histogram.png"
    plt.savefig(output_path, dpi=300)


def genre_hist(data):
    info_dict={}
    for x in data:
        for g in x["genres"]:
            if g in info_dict:
                info_dict[g]+=1
            else:
                info_dict[g]=1

    print(dict(sorted(info_dict.items(), key=lambda x: x[1], reverse=True)))



def lang_hist(data):
    info_dict={}
    for x in data:
        for g in x["languages"]:
            if g in info_dict:
                info_dict[g]+=1
            else:
                info_dict[g]=1

    print(dict(sorted(info_dict.items(), key=lambda x: x[1], reverse=True)))


def country_hist(data):
    info_dict={}
    for x in data:
        for g in x["countries"]:
            if g in info_dict:
                info_dict[g]+=1
            else:
                info_dict[g]=1

    print(dict(sorted(info_dict.items(), key=lambda x: x[1], reverse=True)))


if __name__ == "__main__":
    PLOT_DIR="assets/figures"
    MIN_WORDS=10
    MAX_WORDS=1000
    MIN_RUN_TIME=20
    MAX_RUN_TIME=200
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    import json
    path_list=[Path(f"data/{x}") for x in sorted(os.listdir("data")) if x.startswith("all_movie_info") and x.endswith(".json")]
    data=[]
    for path in path_list:
        with open(path, "r", encoding="utf-8") as f:
            data.extend(json.load(f))

    # word_cloud(data)
    # summ_len_hist(data)
    # release_year_hist(data)
    # run_time_hist(data)
    genre_hist(data)
    lang_hist(data)
    country_hist(data)
    