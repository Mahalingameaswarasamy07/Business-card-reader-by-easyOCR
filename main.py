import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector as sql
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re

# Page configuration
st.set_page_config(page_title="Business card reader | By Mahalingam",layout="wide",)
st.markdown("<h1 style='text-align: center; color: white;'>Business Card Reader</h1>", unsafe_allow_html=True)

# OCR object
reader = easyocr.Reader(['en'])

# Database configuration
mydb = sql.connect(host="localhost",
                   user="root",
                   password="mysqlpassword1!",
                   database= "bizcard_db"
                  )
mycursor = mydb.cursor(buffered=True)

mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

# helper functions
def img_to_binary(file):
    with open(file, 'rb') as file:
        binaryData = file.read()
    return binaryData

def save_card(uploaded_card):
    with open(os.path.join("uploaded_cards",uploaded_card.name), "wb") as f:
        f.write(uploaded_card.getbuffer()) 

def image_preview(image,res): 
    for (bbox, text, prob) in res: 
        # unpack the bounding box
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        cv2.rectangle(image, tl, br, (0, 255, 0), 2)
        cv2.putText(image, text, (tl[0], tl[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    plt.rcParams['figure.figsize'] = (8,8)
    plt.axis('off')
    plt.imshow(image)

def get_data(res):
    for ind,i in enumerate(res):
        if "www " in i.lower() or "www." in i.lower():
            data["website"].append(i)
        elif "WWW" in i:
            data["website"] = res[4] +"." + res[5]
        elif "@" in i:
            data["email"].append(i)
        elif "-" in i:
            data["mobile_number"].append(i)
            if len(data["mobile_number"]) ==2:
                data["mobile_number"] = " & ".join(data["mobile_number"])
        elif ind == len(res)-1:
            data["company_name"].append(i)
        elif ind == 0:
            data["card_holder"].append(i)
        elif ind == 1:
            data["designation"].append(i)
        if re.findall('^[0-9].+, [a-zA-Z]+',i):
            data["area"].append(i.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+',i):
            data["area"].append(i)

        match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
        match3 = re.findall('^[E].*',i)
        if match1:
            data["city"].append(match1[0])
        elif match2:
            data["city"].append(match2[0])
        elif match3:
            data["city"].append(match3[0])
            
        state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
        if state_match:
                data["state"].append(i[:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
            data["state"].append(i.split()[-1])
        if len(data["state"])== 2:
            data["state"].pop(0)
                
        if len(i)>=6 and i.isdigit():
            data["pin_code"].append(i)
        elif re.findall('[a-zA-Z]{9} +[0-9]',i):
            data["pin_code"].append(i[10:])

def create_df(data):
    df = pd.DataFrame(data)
    return df

# Page switch option
st.markdown("#     ")      
selected = option_menu(None, ["Data extract","Update data","View all"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "0px", "--hover-color": "#f2b879", "transition": "color 0.3s ease, background-color 0.3s ease"},
                               "container" : {"max-width": "6000px", "padding": "10px", "border-radius": "5px"},
                               "nav-link-selected": {"background-color": "#f28e22", "color": "white"}})

# Data extract
if selected == "Data extract":
    col1,col2 = st.columns(2,gap="large")
    with col1:
        st.markdown("### Choose File")
        st.markdown("#     ")
        uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])   
        
        if uploaded_card is not None:  
            save_card(uploaded_card)

        with col2:
            if uploaded_card is not None:
                st.markdown("### Raw Image")
                st.image(uploaded_card)
 
    if uploaded_card is not None:
        st.markdown("#     ")
        st.markdown("#     ")
        with st.spinner("please wait.."):
            st.set_option('deprecation.showPyplotGlobalUse', False)
            saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
            image = cv2.imread(saved_img)
            res = reader.readtext(saved_img)
            st.markdown("### Processed Image")
            st.pyplot(image_preview(image,res))  
            saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
            result = reader.readtext(saved_img,detail = 0,paragraph=False)
            
            data = {"company_name" : [],
                    "card_holder" : [],
                    "designation" : [],
                    "mobile_number" :[],
                    "email" : [],
                    "website" : [],
                    "area" : [],
                    "city" : [],
                    "state" : [],
                    "pin_code" : [],
                    "image" : img_to_binary(saved_img)
                    }

            get_data(result)
            df = create_df(data)
            
        if df is not None:
            with st.spinner("we are preparing data for upload"): 
                st.markdown("#     ")  
                st.markdown("""<style>.stButton button {float: right;}</style>""",unsafe_allow_html=True)
                if st.button(":green[**Upload to DB**]"):
                    for i,row in df.iterrows():
                        sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                        mycursor.execute(sql, tuple(row))
                        mydb.commit()
                    st.success("#### Data Updation successfully")
 
if selected == "Update data":
    selected_sub = option_menu(None, ["Update","Delete"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "15px", "text-align": "centre", "margin": "0px", "--hover-color": "#f2b879", "transition": "color 0.3s ease, background-color 0.3s ease"},
                               "container" : {"max-width": "6000px", "padding": "10px", "border-radius": "5px"},
                               "nav-link-selected": {"background-color": "#f28e22", "color": "white"}})
    
    # Data update 
    if selected_sub == "Update":
        mycursor.execute("SELECT card_holder FROM card_data")
        result = mycursor.fetchall()
        business_cards = {}
        for row in result:
            business_cards[row[0]] = row[0]
        selected_card = st.selectbox("Select", list(business_cards.keys()))
        st.markdown("#### Update below details")
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                        (selected_card,))
        result = mycursor.fetchone()

        cols1,cols2,cols3,cols4=st.columns(4,gap="large")
        with cols1:
            company_name = st.text_input("Company_Name", result[0])
        with cols2:
            card_holder = st.text_input("Card_Holder", result[1])
        with cols3:
            designation = st.text_input("Designation", result[2])
        with cols4:
            mobile_number = st.text_input("Mobile_Number", result[3])
        
        cols5,cols6,cols7,cols8=st.columns(4,gap="large")
        with cols5:
            email = st.text_input("Email", result[4])
        with cols6:
            website = st.text_input("Website", result[5])
        with cols7:
            area = st.text_input("Area", result[6])
        with cols8:
            city = st.text_input("City", result[7])
            
        cols9,cols10=st.columns(2,gap="large")
        with cols9:
            state = st.text_input("State", result[8])
        with cols10:
            pin_code = st.text_input("Pin_Code", result[9])
        st.markdown("""<style>.stButton button {float: right;}</style>""",unsafe_allow_html=True)
        if st.button(":green[**Update**]"):
            mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
            mydb.commit()
            st.success("Updation successfully")

    try:
        # Data delete
        if selected_sub == "Delete":
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select", list(business_cards.keys()))
            st.markdown("""<style>.stButton button {float: right;}</style>""",unsafe_allow_html=True)
            if st.button(":red[**Delete**]"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted successfully")
    except:
        st.warning("There is no data available in the database")
    
# view all data   
if selected == "View all":
    mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
    updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
    st.write(updated_df)


