import os
import json
from tqdm import tqdm
import re

def norm_string(s):
    s = s.lower()                         
    s = re.sub(r'[^a-z0-9]', '', s)  
    return s     

def main(chunk_idx,chunk_size):
    processed_data=[]
    save_path=f"data/all_movie_info_{chunk_idx:02d}.json"
    cms_interme_dir="data/intermediate/cms"
    
    cms_meta=f"{cms_interme_dir}/movie.metadata.json"
    with open(cms_meta,"r") as f:
        cms_meta_data=json.load(f)
    print("len of cms_meta_data: ",len(cms_meta_data))
        
    cms_character=f"{cms_interme_dir}/character.metadata.json"
    with open(cms_character,"r") as f:
        cms_charactor_data=json.load(f)
    print("len of cms_charactor_data: ",len(cms_charactor_data))
    
    cms_plot_sum=f"{cms_interme_dir}/plot_summaries.json"
    with open(cms_plot_sum,"r") as f:
        cms_plot_summ_data=json.load(f)
    print("len of cms_plot_summ_data: ",len(cms_plot_summ_data))

    # imdb_basic="intermediate/imdb/title.basics.json"
    # with open(imdb_basic,"r") as f:
    #     imdb_basic_data=json.load(f)
    # print("len of imdb_basic_data: ",len(imdb_basic_data))
    
    # imdb_rating="intermediate/imdb/title.ratings.json"
    # with open(imdb_rating,"r") as f:
    #     imdb_rating_data=json.load(f)
    # print("len of imdb_rating_data: ",len(imdb_rating_data))
    
    # imdb_crew="intermediate/imdb/title.crew.json"
    # with open(imdb_crew,"r") as f:
    #     imdb_crew_data=json.load(f)
    # print("len of imdb_crew_data: ",len(imdb_crew_data))
    
    # imdb_people_name_basics="intermediate/imdb/name.basics.json"
    # with open(imdb_people_name_basics,"r") as f:
    #     imdb_people_name_basics_data=json.load(f)
    # print("len of imdb_people_name_basics_data: ",len(imdb_people_name_basics_data))
    
    begin_idx=chunk_idx*chunk_size
    end_idx=(chunk_idx+1)*chunk_size
    if begin_idx>len(cms_plot_summ_data):
        return
    if end_idx>len(cms_plot_summ_data):
        end_idx=len(cms_plot_summ_data)
    cms_plot_summ_data=cms_plot_summ_data[begin_idx:end_idx]
    
    for item in tqdm(cms_plot_summ_data):
        new_item={
            "wiki_movie_id": "",
            "freebase_movie_id": "",
            "movie_name": "",
            "summary": "",
            "release_date": "",
            "year":"",
            "runtime": "",
            "languages": [],
            "countries": [],
            "genres": [],
            "box_office_revenue": "",
            "character_actor_map": {},
        }
        
        new_item["wiki_movie_id"]=item['wiki_movie_id']
        new_item["summary"]=item['plot_summary']
        
        id=item['wiki_movie_id']
        
        for x in cms_meta_data:
            if x['wiki_movie_id']==id:
                new_item['freebase_movie_id']=x['freebase_movie_id']
                new_item['movie_name']=x['movie_name']
                new_item['release_date']=x['movie_release_date']
                new_item['runtime']=x['movie_runtime']
                new_item['languages']=x['movie_languages']
                new_item['countries']=x['movie_countries']
                new_item['genres']=x['movie_genres']
                new_item['box_office_revenue']=x['movie_box_office_revenue']
                
                release_date=new_item['release_date']
                year = None
                if len(release_date) >= 4 and release_date[:4].isdigit():
                    year = int(release_date[:4])
                new_item["year"]=year
        
        for y in cms_charactor_data:
            if y["wiki_movie_id"]==id:
                new_item['character_actor_map'][y['character_name']]=y['actor_name']
                
        processed_data.append(new_item)

    with open(save_path,"w",encoding='utf-8') as f:
        json.dump(processed_data,f,indent=4,ensure_ascii=False)
    


if __name__ == "__main__":
    # len of cms_meta_data:  81740
    # len of cms_charactor_data:  450668
    # len of cms_plot_summ_data:  42306   <-- main data
    
    num_plot_summ=42306
    chunk_size=10000
    num_chunk=num_plot_summ//chunk_size
    for chunk_idx in range(num_chunk+1):
        main(chunk_idx,chunk_size)