import os
import json
from tqdm import tqdm
import re

def norm_string(s):
    s = s.lower()                         
    s = re.sub(r'[^a-z0-9]', '', s)  
    return s     

def main(chunk_idx,chunk_size):
    merged_data=[]
    merge_path=f"all_info_chunk{chunk_idx}.json"
    num_found_in_imdb=0
    
    imdb_basic="imdb/title.basics.json"
    with open(imdb_basic,"r") as f:
        imdb_basic_data=json.load(f)
    imdb_rating="imdb/title.ratings.json"
    with open(imdb_rating,"r") as f:
        imdb_rating_data=json.load(f)
    cms_meta="cms/movie.metadata.json"
    with open(cms_meta,"r") as f:
        cms_meta_data=json.load(f)
    cms_character="cms/character.metadata.json"
    with open(cms_character,"r") as f:
        cms_charactor_data=json.load(f)
        
    cms_plot_sum="cms/plot_summaries.json"
    with open(cms_plot_sum,"r") as f:
        plot_summ_data=json.load(f)

    begin_idx=chunk_idx*chunk_size
    end_idx=(chunk_idx+1)*chunk_size
    plot_summ_data=plot_summ_data[begin_idx:end_idx]


    for item in tqdm(plot_summ_data):
        new_item={
            "wiki_movie_id": "",
            "freebase_movie_id": "",
            "imdb_movie_id": "",
            "movie_name": "",
            "release_date": "",
            "summary": "",
            "runtime": "",
            "languages": [],
            "countries": [],
            "genres": [],
            "character_actor_map": {},
            "box_office_revenue": "",
            "rating": "",
            "rating_votes": "",
            "director": ""
        }
        
        name=""
        id=item['wiki_movie_id']
        
        new_item["wiki_movie_id"]=item['wiki_movie_id']
        new_item["summary"]=item['plot_summary']
        for x in cms_meta_data:
            if x['wiki_movie_id']==id:
                name=x['movie_name']
                new_item['freebase_movie_id']=x['freebase_movie_id']
                new_item['movie_name']=x['movie_name']
                new_item['release_date']=x['movie_release_date']
                new_item['runtime']=x['movie_runtime']
                new_item['languages']=x['movie_languages']
                new_item['countries']=x['movie_countries']
                new_item['genres']=x['movie_genres']
                new_item['box_office_revenue']=x['movie_box_office_revenue']
        
        for y in cms_charactor_data:
            if y["wiki_movie_id"]==id:
                new_item['character_actor_map'][y['character_name']]=y['actor_name']
        
        for z in imdb_basic_data:
            if norm_string(name)==norm_string(z['primaryTitle']):
                num_found_in_imdb+=1
                imdb_movie_id=z['tconst']
                new_item["imdb_movie_id"]=imdb_movie_id
                for w in imdb_rating_data:
                    if w['tconst']==imdb_movie_id:
                        new_item["rating"]=w['averageRating']
                        new_item["num_votes"]=w['numVotes']
        
        merged_data.append(new_item)
        
    with open(merge_path,"w",encoding='utf-8') as f:
        json.dump(merged_data,f,indent=4,ensure_ascii=False)
    print(num_found_in_imdb)


if __name__ == "__main__":
    chunk_idx=0
    chunk_size=5000
    main(chunk_idx,chunk_size)