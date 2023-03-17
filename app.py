from flask import Flask, render_template, url_for, redirect, request
import pandas as pd
import spacy
from specialities import sp_str
from threading import Thread
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime
from datetime import date as current_date
nlp = spacy.load("en_core_sci_lg")

def ttsh():
    print("TTSH Thread Started...")
    ttsh_results = []
    base_url = "https://www.ttsh.com.sg/about-ttsh/ttsh-events/Pages/default.aspx"
    r = requests.get(base_url)
    soup = BeautifulSoup(r.text, "html.parser")
    paging = soup.find("div", {"class": "pagingOf"}).text
    n_pages = int(paging.split(" of ")[-1])
    for i in range(1, n_pages + 1):
        url = f"https://www.ttsh.com.sg/about-ttsh/ttsh-events/Pages/default.aspx?sr_category=&sr_datey=&sr_datem=&pgNo={i}"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        section = soup.find("section", {"class": "listing"})
        articles = section.find_all("article")
        for article in articles:
            name = article.find("h2").text
            keywords = get_sim(name)
            details_url = "https://www.ttsh.com.sg" + article.find("h2").find("a")['href']
            r_details = requests.get(details_url)
            soup_details = BeautifulSoup(r_details.text, "html.parser")
            main_article = soup_details.find("article")
            main_divs = main_article.find_all("div", {"class": "item-wrapper"})
            details = []
            for main_div in main_divs:
                label = main_div.find("div", {"class": "item-label"}, recursive = False).text
                if label == "Synopsis" or label == "Description":
                    value = main_div.find("div", {"class": "item-value"}, recursive = False).decode_contents()
                else:
                    value = main_div.find("div", {"class": "item-value"}, recursive = False).text
                details.append([label, value])
            start_year = None
            end_year = None
            start_month = None
            end_month = None
            start_date = None
            end_date = None
            start_time = None
            end_time = None
            year_present = False
            month_present = False
            date_present = False
            time_present = False
            description_present = False
            temp_time = None
            description = None
            add_info = None
            venue = None
            mode = None
            fee_type = None
            fees = 0.00
            saot_fees = None
            non_saot_fees = None
            contact_person = None
            contact_email = None
            register_url = details_url
            for detail in details:
                if "Date" in detail[0] and "Time" in detail[0]:
                    date = detail[1].replace("\r", "").replace("\n", " ").split(" / ")[0]
                    if len(date) > 0:
                        years = re.findall("[1-3][0-9][0-9][0-9]", date)
                        if len(years) > 0:
                            year_present = True
                            if len(years) == 1:
                                start_year = int(years[0])
                                end_year = start_year
                            elif len(years) == 2:
                                if int(years[0]) <= int(years[1]):
                                    start_year = int(years[0])
                                    end_year = int(years[1])
                                else:
                                    start_year = int(years[0])
                                    end_year = int(years[0])
                    if year_present == True:
                        date = re.sub(" [1-3][0-9][0-9][0-9]", "", date)
                        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                        months = []
                        for month in months_list:
                            if month in date:
                                months.append(month)
                        if len(months) > 0:
                            month_present = True
                            if len(months) == 1:
                                start_month = months[0]
                                end_month = months[0]
                            else:
                                start_month = months[0]
                                end_month = months[1]
                    if month_present == True:
                        date = date.replace(f" {start_month}", "")
                        date = date.replace(f" {end_month}", "")
                        date = date.replace(f"{start_month}", "")
                        date = date.replace(f"{end_month}", "")
                        if "to be confirmed" not in date.lower():
                            if " - " in date:
                                if len(date.split(" ")) == 3:
                                    date_present = True
                                    start_date = int(date.split(" - ")[0])
                                    end_date = int(date.split(" - ")[1])
                            elif " to " in date:
                                if len(date.split(" ")) == 3:
                                    date_present = True
                                    start_date = int(date.split(" to ")[0])
                                    end_date = int(date.split(" to ")[1])
                            elif " and " in date:
                                if len(date.split(" ")) == 3:
                                    date_present = True
                                    start_date = int(date.split(" and ")[0])
                                    end_date = int(date.split(" and ")[1])
                            elif date != "":
                                date_present = True
                                start_date = int(date)
                                end_date = int(date)
                    if len(detail[1].replace("\r", "").replace("\n", " ").split(" / ")) > 1:
                        temp_time = " / ".join(detail[1].replace("\r", "").replace("\n", " ").split(" / ")[1:])
                        if "to be confirmed" not in temp_time.lower():
                            time_present = True
                            if len(temp_time.split(" / ")) == 1:
                                temp_time = temp_time.lower()
                                temp_time_new = []
                                if " - " in temp_time:
                                    temp_time = temp_time.split(" - ")
                                    for item in temp_time:
                                        temp_time_new.append(item.replace(" ", "").replace(".", ":"))
                                    start_time = temp_time_new[0]
                                    end_time = temp_time_new[1]
                                elif " to " in temp_time:
                                    temp_time = temp_time.split(" to ")
                                    for item in temp_time:
                                        temp_time_new.append(item.replace(" ", "").replace(".", ":"))
                                    start_time = temp_time_new[0]
                                    end_time = temp_time_new[1]
                            else:
                                temp_time_1 = temp_time.split(" / ")[0]
                                temp_time_2 = temp_time.split(" / ")[1]
                                temp_time_1 = temp_time_1.split(": ")
                                temp_time_2 = temp_time_2.split(": ")
                                temp_time_1_2 = temp_time_1[1].lower()
                                temp_time_2_2 = temp_time_2[1].lower()
                                temp_time_new_1 = []
                                temp_time_new_2 = []
                                if " – " in temp_time_1_2:
                                    temp_time_1_2 = temp_time_1_2.split(" – ")
                                    for item in temp_time_1_2:
                                        temp_time_new_1.append(item.replace(" ", "").replace(".", ":"))
                                elif " to " in temp_time_1_2:
                                    temp_time_1_2 = temp_time_1_2.split(" to ")
                                    for item in temp_time_1_2:
                                        temp_time_new_1.append(item.replace(" ", "").replace(".", ":"))
                                if " – " in temp_time_2_2:
                                    temp_time_2_2 = temp_time_2_2.split(" – ")
                                    for item in temp_time_2_2:
                                        temp_time_new_2.append(item.replace(" ", "").replace(".", ":"))
                                elif " to " in temp_time_2_2:
                                    temp_time_2_2 = temp_time_2_2.split(" to ")
                                    for item in temp_time_2_2:
                                        temp_time_new_2.append(item.replace(" ", "").replace(".", ":"))
                                time_label_1 = temp_time_1[0]
                                time_label_2 = temp_time_2[0]
                                while time_label_1[0] == " ":
                                    time_label_1 = time_label_1[1:]
                                while time_label_2[0] == " ":
                                    time_label_2 = time_label_2[1:]
                                time_label_1 = time_label_1.title()
                                time_label_2 = time_label_2.title()
                                if temp_time_new_1[0][-1] == ":":
                                    start_time = f'{temp_time_new_1[0][:-1]} ({time_label_1}); {temp_time_new_2[0]} ({time_label_2})'
                                elif temp_time_new_2[0][-1] == ":":
                                    start_time = f'{temp_time_new_1[0]} ({time_label_1}); {temp_time_new_2[0][:-1]} ({time_label_2})'
                                else:
                                    start_time = f'{temp_time_new_1[0]} ({time_label_1}); {temp_time_new_2[0]} ({time_label_2})'
                                if temp_time_new_1[1][-1] == ":":
                                    end_time = f'{temp_time_new_1[1][:-1]} ({time_label_1}); {temp_time_new_2[1]} ({time_label_2})'
                                elif temp_time_new_2[1][-1] == ":":
                                    end_time = f'{temp_time_new_1[1]} ({time_label_1}); {temp_time_new_2[1][:-1]} ({time_label_2})'
                                else:
                                    end_time = f'{temp_time_new_1[1]} ({time_label_1}); {temp_time_new_2[1]} ({time_label_2})'
                        else:
                            temp_time = None
                elif detail[0] == "Synopsis":
                    if "NIL" not in detail[1]:
                        description = detail[1]
                elif detail[0] == "Description":
                    if "NIL" not in detail[1]:
                        add_info = detail[1]
                        if description == None and add_info != None:
                            description = add_info
                            add_info = None
                        if description != None:
                            description_present = True
                elif detail[0] == "Event Fees":
                    if "$" in detail[1]:
                        fee_type = "Paid"
                        fees = float(detail[1].split("$")[1])
                    elif add_info != None and "$" in add_info:
                        fee_type = "Paid"
                        saot_fees = float(re.findall('[1-9][0-9][0-9]', add_info)[0])
                        non_saot_fees = float(re.findall('[1-9][0-9][0-9]', add_info)[1])
                        fees = f'{str(saot_fees)} (SAOT Member); {str(non_saot_fees)} (Non-SAOT Member)'
                    else:
                        fee_type = "Free"
                elif detail[0] == "Venue":
                    if "via zoom" in detail[1].lower() or "virtual" in detail[1].lower() or "over zoom" in detail[1].lower():
                        mode = "Virtual"
                    else:
                        mode = "Face-to-Face"
                        if "to be confirmed" not in detail[1].lower():
                            if "TTSH " in detail[1]:
                                venue = detail[1].replace("TTSH ", "Tan Tock Seng Hospital, ")
                            elif detail[1] == "TTSH":
                                venue = "Tan Tock Seng Hospital"
                            else:
                                venue = detail[1]
                elif detail[0] == "Contact Person":
                    if "TTSH" in detail[1]:
                        contact_person = detail[1].replace("TTSH", "Tan Tock Seng Hospital")
                    else:
                        contact_person = detail[1]
                elif detail[0] == "Email":
                    contact_email = detail[1]
            if month_present == True and year_present == True and description_present == True:
                for row in keywords:
                    ttsh_results.append([
                        name,
                        "Tan Tock Seng Hospital",
                        row[0],
                        row[1],
                        row[2],
                        date_present,
                        description_present,
                        start_year,
                        int(months_list.index(start_month) + 1),
                        start_date,
                        end_year,
                        int(months_list.index(end_month) + 1),
                        end_date,
                        time_present,
                        start_time,
                        end_time,
                        description,
                        add_info,
                        fee_type,
                        fees,
                        saot_fees,
                        non_saot_fees,
                        mode,
                        venue,
                        contact_person,
                        contact_email
                    ])
    ttsh_df = pd.DataFrame(ttsh_results, columns = [
        'event name',
        'organiser',
        'speciality',
        'keyword',
        'similarity',
        'date present',
        'description present',
        'start year',
        'start month',
        'start date',
        'end year',
        'end month',
        'end date',
        'time present',
        'start time',
        'end time',
        'description',
        'add info',
        'fee type',
        'fees',
        'saot fees',
        'non saot fees',
        'mode',
        'venue',
        'contact person',
        'contact email'
    ])
    ttsh_df.to_csv("resources/ttsh.csv")
    return print("TTSH Thread Ended...")

def create_app():
    app = Flask("__name__")
    # async_ttsh = Thread(target = ttsh)
    # async_ttsh.start()
    return app

app = create_app()

def create_datetime(df):
    if df['date present'] == False:
        return datetime(df['start year'], df['start month'], 30)
    else:
        return datetime(df['start year'], df['start month'], int(df['start date']))

@app.route("/")
def hello():
    ttsh_df = pd.read_csv("resources/ttsh.csv")
    ttsh_df = ttsh_df[[
        'event name',
        'organiser',
        'speciality',
        'keyword',
        'similarity',
        'date present',
        'description present',
        'start year',
        'start month',
        'start date',
        'end year',
        'end month',
        'end date',
        'time present',
        'start time',
        'end time',
        'description',
        'add info',
        'fee type',
        'fees',
        'saot fees',
        'non saot fees',
        'mode',
        'venue',
        'contact person',
        'contact email'
    ]]
    ttsh_df['datetime'] = ttsh_df.apply(create_datetime, axis = 1)
    current_datetime = current_date.today()
    ttsh_df = ttsh_df[ttsh_df['datetime'].dt.date >= current_datetime]
    ttsh_df = ttsh_df.sort_values('datetime', ascending = True)
    ttsh_df = ttsh_df.drop_duplicates(subset = ['event name'])
    upcoming_events = ttsh_df.head(6)
    upcoming_events_html = events_html_generator(upcoming_events)
    return render_template("index.html", upcoming_events_html = upcoming_events_html)

def get_price_filter(x):
    x_int = 0
    try:
        x_int = float(x)
    except:
        x_int = float(x.split("; ")[-1].split(" ")[0])
    return x_int

def get_keyword_sim(x, keyword):
    nlp_x = nlp(x)
    nlp_keyword = nlp(keyword)
    return nlp_keyword.similarity(nlp_x)

@app.route("/browse-events/<start>", methods = ['GET', 'POST'])
def events_search(start):
    keyword = ""
    category = "Category"
    month = ""
    price = ""
    search_criteria = []
    mode = "Mode"
    if int(start) == 1:
        keyword = request.form.to_dict()['keyword']
        category = request.form.to_dict()['category']
        month = request.form.to_dict()['month']
        price = request.form.to_dict()['price']
        mode = request.form.to_dict()['mode']
    ttsh_df = pd.read_csv("resources/ttsh.csv")
    ttsh_df = ttsh_df[[
        'event name',
        'organiser',
        'speciality',
        'keyword',
        'similarity',
        'date present',
        'description present',
        'start year',
        'start month',
        'start date',
        'end year',
        'end month',
        'end date',
        'time present',
        'start time',
        'end time',
        'description',
        'add info',
        'fee type',
        'fees',
        'saot fees',
        'non saot fees',
        'mode',
        'venue',
        'contact person',
        'contact email'
    ]]
    if keyword != "" and category != "Category":
        ttsh_df = ttsh_df[ttsh_df['speciality'] == category.lower()]
        ttsh_df['keyword similarity'] = ttsh_df['keyword'].apply(lambda x: get_keyword_sim(x, keyword.lower()))
        ttsh_df['overall similarity'] = (ttsh_df['similarity'] + ttsh_df['keyword similarity']) / 2
        ttsh_df = ttsh_df.sort_values('overall similarity', ascending = False)
        ttsh_df = ttsh_df[ttsh_df['overall similarity'] >= 0.45]
        search_criteria.append(f"<strong>{keyword.lower()}</strong> (keyword)")
        search_criteria.append(f"<strong>{category}</strong> (category)")
    elif keyword != "" and category == "Category":
        ttsh_df['keyword similarity'] = ttsh_df['keyword'].apply(lambda x: get_keyword_sim(x, keyword.lower()))
        ttsh_df = ttsh_df.sort_values('keyword similarity', ascending = False)
        ttsh_df = ttsh_df[ttsh_df['keyword similarity'] >= 0.5]
        search_criteria.append(f"<strong>{keyword.lower()}</strong> (keyword)")
    elif keyword == "" and category != "Category":
        ttsh_df = ttsh_df[ttsh_df['speciality'] == category.lower()]
        ttsh_df = ttsh_df.sort_values('similarity', ascending = False)
        ttsh_df = ttsh_df[ttsh_df['similarity'] >= 0.4]
        search_criteria.append(f"<strong>{category}</strong> (category)")
    if month != "":
        search_month = int(month.split("-")[1])
        search_year = int(month.split("-")[0])
        ttsh_df = ttsh_df[(ttsh_df['start month'] >= search_month) & (ttsh_df['start year'] >= search_year)]
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        search_criteria.append(f"<strong>{months_list[search_month - 1]} {search_year}</strong> (month, year)")
    if mode != "Mode":
        ttsh_df = ttsh_df[ttsh_df['mode'] == mode]
        search_criteria.append(f"<strong>{mode}</strong> (mode)")
    if price != "":
        if int(price) == 0:
            ttsh_df = ttsh_df[ttsh_df['fee type'] == "Free"]
        else:
            ttsh_df['price'] = ttsh_df['fees'].apply(lambda x: get_price_filter(x))
            ttsh_df = ttsh_df[ttsh_df['price'] <= int(price)]
        search_criteria.append(f"<strong>SG${price}</strong> (price)")
    ttsh_df = ttsh_df.drop_duplicates(subset = ['event name'])
    events_html = events_html_generator(ttsh_df)
    search_criteria = "You have searched for " + ", ".join(search_criteria)
    if ttsh_df.empty:
        search_criteria = "No events found"
    if start == '0':
        search_type = 0
    elif start == '1':
        search_type = 1
    return render_template("search.html", events_html = events_html, search_criteria = search_criteria, search_type = search_type)

def events_html_generator(df):
    html = ""
    df_list = df.values.tolist()
    for item in df_list:
        description = BeautifulSoup(item[16], "html.parser")
        description = description.text
        date = ""
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if item[5] == True:
            date = f'{int(item[9])} {months_list[int(item[8]) - 1]} {item[7]} - {int(item[12])} {months_list[int(item[11]) - 1]} {item[10]}'
        else:
            date = f'{months_list[int(item[8]) - 1]} {item[7]} - {months_list[int(item[11]) - 1]} {item[10]}'
        price = ""
        if item[18] == "Free":
            price = "Free"
        else:
            price = "SG$" + item[19]
            price = price.replace("; ", "; SG$")
        time = ""
        if item[13] == True:
            time = f'{item[14]} - {item[15]}'
        else:
            time = 'To Be Determined'
        location = ""
        if item[22] == "Virtual":
            location = "Virtual"
        else:
            location = item[23]
        html += f"""
            <div class="row">
                <div class="col-3">
                    <img class="event_image" src="https://www.americanoceans.org/wp-content/uploads/2021/06/shutterstock_1807037047-scaled.jpg" alt="">
                </div>
                <div class="col-9">
                    <div class="event_container">
                        <div class="row">
                            <div class="col-10">
                                <p class="event_name">{item[0]}</p>
                                <p class="event_description">{(description[:75] + "...") if len(description) > 75 else description}</p>
                                <p class="event_details"><strong>Date:</strong>&nbsp;{date}&emsp;<strong>Time:</strong>&nbsp;{time}&emsp;<strong>Price:</strong>&nbsp;{price}&emsp;<strong>Location:</strong>&nbsp;{location}&emsp;<span class="event_organiser"><strong>Hosted by&nbsp;</strong>{item[1]}</span></p>
                            </div>
                            <div class="col-2" style="padding: 0px;">
                                <a href="/events-details/{item[0]}"><button class="event_button">Find Out More</button></a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <br><br>
        """
    return html

def get_sim(name):
    sp_list = sp_str.lower().split("\n")
    nlp_name = name.lower()
    for chr in nlp_name:
        if chr not in " abcdefghijklmnopqrstuvwxyz ":
            nlp_name = nlp_name.replace(chr, " ")
    entities = list(nlp(nlp_name).ents)
    df_list = []
    for sp in sp_list:
        nlp_sp = nlp(sp)
        for ent in entities:
            nlp_ent = nlp(ent.text)
            df_list.append([sp, ent.text, nlp_sp.similarity(nlp_ent)])
    df_list_new = []
    df = pd.DataFrame(df_list, columns = ['Speciality', 'Word', 'Similarity']).sort_values(['Similarity'], ascending = False)
    for ent in entities:
        most_sim = df[df['Word'] == ent.text].values.tolist()[0]
        df_list_new.append(most_sim)
    df_new = pd.DataFrame(df_list_new, columns = ['Speciality', 'Word', 'Similarity']).sort_values(['Similarity'], ascending = False)
    return df_new.values.tolist()

@app.route("/events-details/<event_name>", methods = ['POST', 'GET'])
def event_details(event_name):
    ttsh_df = pd.read_csv("resources/ttsh.csv")
    ttsh_df = ttsh_df[[
        'event name',
        'organiser',
        'speciality',
        'keyword',
        'similarity',
        'date present',
        'description present',
        'start year',
        'start month',
        'start date',
        'end year',
        'end month',
        'end date',
        'time present',
        'start time',
        'end time',
        'description',
        'add info',
        'fee type',
        'fees',
        'saot fees',
        'non saot fees',
        'mode',
        'venue',
        'contact person',
        'contact email'
    ]]
    event_df = ttsh_df[ttsh_df['event name'] == event_name]
    event_df = event_df.drop_duplicates(subset = ['event name'])
    event = event_df.values.tolist()[0]
    description = BeautifulSoup(event[16], "html.parser")
    description_final = ""
    paras = description.find_all("p", recursive = False)
    register_url = ""
    paras_final = []
    for para in paras:
        if not para.find("a"):
            paras_final.append(para.text)
        else:
            register_url = para.find("a")['href']
    description_final += "<br><br>".join(paras_final)
    ul = description.find("ul")
    ol = description.find("ol")
    if ul:
        lis = ul.find_all("li")
        for i in range(len(lis)):
            description_final += "<br>" + f"{str(i + 1)}) {lis[i].text}"
    if ol:
        lis = ol.find_all("li")
        for i in range(len(lis)):
            description_final += "<br>" + f"{str(i + 1)}) {lis[i].text}"
    date = ""
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    if event[5] == True:
        date = f'{int(event[9])} {months_list[int(event[8]) - 1]} {event[7]} - {int(event[12])} {months_list[int(event[11]) - 1]} {event[10]}'
    else:
        date = f'{months_list[int(event[8]) - 1]} {event[7]} - {months_list[int(event[11]) - 1]} {event[10]}'
    price = ""
    if event[18] == "Free":
        price = "Free"
    else:
        price = "SG$" + event[19]
        price = price.replace("; ", "; SG$")
    time = ""
    if event[13] == True:
        time = f'{event[14]} - {event[15]}'
    else:
        time = 'To Be Determined'
    location = ""
    if event[22] == "Virtual":
        location = "Virtual"
    else:
        location = event[23]
    return render_template("events_details.html", event_name = event_name, description = description_final, date = date, time = time, price = price, venue = location, register_url = register_url)