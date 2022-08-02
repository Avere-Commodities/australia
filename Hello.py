import streamlit as st
from support_files.quickstart import credentials, download_image
from streamlit_charts import deviation_charts


st.set_page_config(page_title="Australia Weather Maps", layout='wide')
creds = credentials()


def main():   
    st.markdown(f"""#### Weather Summary""")
    col1, col2 = st.columns(2)
    tp = download_image(creds, filename='australia_tp.png')
    t2m = download_image(creds, filename='australia_t2m.png')
    m, w = deviation_charts()
    col1.image(tp)
    col2.image(t2m)
    col1.plotly_chart(w, use_container_width=True)
    col2.plotly_chart(m, use_container_width=True)
    st.markdown(f"""#### Production by County""")
    col1, col2 = st.columns(2)
    col1.image('./support_files/production_charts/aus_wheat.jpg')
    col2.image('./support_files/production_charts/aus_barley.jpg')
    
if __name__ == '__main__':
    main()
