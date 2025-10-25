import csv
import json
from tqdm import tqdm
import os
from ast import literal_eval
import re

def sanitize(obj):
    if isinstance(obj, str):
        return _surrogate_re.sub('', obj)
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


def imdb_tsv_to_json():
    raw_dir="raw/imdb_tsv"
    save_dir="imdb"
    fname_list=[
        "name.basics.tsv",
        "title.akas.tsv",
        "title.basics.tsv",
        "title.crew.tsv",
        "title.episode.tsv",
        "title.principals.tsv",
        "title.ratings.tsv",
    ]
    for fname in fname_list:
        data_list=[]
        with open(f"{raw_dir}/{fname}", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if reader.fieldnames:
                reader.fieldnames = [h.replace("\ufeff", "").strip() for h in reader.fieldnames]
            for i,row in tqdm(enumerate(reader)):
                if max_rows is not None:
                    if i >= max_rows:
                        break
                data_list.append(row)

        os.makedirs(save_dir,exist_ok=True)
        json_path=f"{save_dir}/{fname.replace('tsv','json')}"
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4)
            


def cms_tsv_to_json():
    raw_dir="raw/MovieSummaries"
    save_dir="cms"
    fname_list=[
        "movie.metadata.tsv",
        "character.metadata.tsv",
    ]
    column_name_map={
        "movie":[
                "wiki_movie_id",
                "freebase_movie_id",
                "movie_name",
                "movie_release_date",
                "movie_box_office_revenue",
                "movie_runtime",
                "movie_languages",
                "movie_countries",
                "movie_genres"
            ],
        "character":[
                "wiki_movie_id",
                "freebase_movie_id",
                "movie_release_date",
                "character_name",
                "actor_dob",
                "actor_gender",
                "actor_height",
                "actor_ethnicity",
                "actor_name",
                "actor_age_at_movie_release",
                "freebase_character_map1",
                "freebase_character_map2",
                "freebase_character_map3"
            ],
        
    }
    for fname in fname_list:
        columns=column_name_map[fname.split(".")[0]]
        data_list=[]
        with open(f"{raw_dir}/{fname}", "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if reader.fieldnames:
                reader.fieldnames = [h.replace("\ufeff", "").strip() for h in reader.fieldnames]
            for i,row in tqdm(enumerate(reader)):
                if max_rows is not None:
                    if i >= max_rows:
                        break
                row_dict = dict(zip(columns, row.values())) 
                if "movie_languages" in row_dict:
                    val = literal_eval(row_dict["movie_languages"])
                    if isinstance(val, dict):
                        row_dict["movie_languages"] = list(val.values())
                    else:
                        row_dict["movie_languages"] = val
                if "movie_countries" in row_dict:
                    val = literal_eval(row_dict["movie_countries"])
                    if isinstance(val, dict):
                        row_dict["movie_countries"] = list(val.values())
                    else:
                        row_dict["movie_countries"] = val
                if "movie_genres" in row_dict:
                    val = literal_eval(row_dict["movie_genres"])
                    if isinstance(val, dict):
                        row_dict["movie_genres"] = list(val.values())
                    else:
                        row_dict["movie_genres"] = val
                data_list.append(row_dict)
                
        data_list = sanitize(data_list)
        os.makedirs(save_dir,exist_ok=True)
        json_path=f"{save_dir}/{fname.replace('tsv','json')}"
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4)


def cms_txt_to_json():
    txt_path = "raw/MovieSummaries/plot_summaries.txt"
    json_path = "cms/plot_summaries.json"

    data = []

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in tqdm(f):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                movie_id, plot = parts
                data.append({
                    "wiki_movie_id": movie_id.strip(),
                    "plot_summary": plot.strip()
                })

    with open(json_path, "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2)




if __name__ == "__main__":
    max_rows=1000
    _surrogate_re = re.compile(r'[\ud800-\udfff]')
    
    imdb_tsv_to_json()
    # cms_tsv_to_json()
    # cms_txt_to_json()