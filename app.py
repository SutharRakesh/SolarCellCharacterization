import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import StringIO
import base64
hide_menu = """
<style>
#MainMenu {
    visibility:visible;
}
footer{
    visibility:visible;
}
footer:after{
    content:'Copyright @2023: Rakesh Suthar. for more info, email:rakeshsuthar1996@gmail.com';
    display:block;
    position:relative;
    color:blue;
    padding:1px;
}
<style>
"""

backgroundColor = "#F0F0F0"
st.set_page_config(page_title='Photovoltaic Parameters Calculator', page_icon='📈')
st.title(f"Photovoltaic parameters calculator")

st.markdown(
    """
        <div class="social-links">
            <a href="www.linkedin.com/in/rakesh-suthar-125b3b136" target="_blank">LinkedIn</a>
            <a href="https://twitter.com/Rakeshsuthar645" target="_blank">Twitter</a>
            <a href="https://www.researchgate.net/profile/Rakesh-Suthar" target="_blank">ResearchGate</a>
            <a href="https://VoltageLossAnalysis.streamlit.app" target="_blank">EQE-Jsc and Voltage-loss Calculator</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(hide_menu, unsafe_allow_html=True)
st.caption(f"App developed by [Rakesh Suthar, IIT Delhi](https://sites.google.com/view/rakeshiitd/home)")

# Collect user inputs
st.sidebar.markdown("""
[Example CSV input file](https://drive.google.com/file/d/1O6B1Drh4r7pVmfX8ZOOhRVMHeGH0_qR4/view?usp=drive_link)
""")

# Function to interpolate data
def interpolate_data(original_data, num_new_points):
    x_original = original_data['Voltage'].values
    y_original = original_data['Current'].values

    x_new = np.linspace(x_original.min(), x_original.max(), num_new_points)
    y_new = np.interp(x_new, x_original, y_original)

    new_data = pd.DataFrame({'Voltage': x_new, 'Current': y_new})
    return new_data

# Function to calculate IV curve and PCE
def calculate_pce(area_cm2, input_power_mw_cm2, data):
    # Generate 1000 new data points for Voltage and Current
    num_new_points = 1000
    new_data = interpolate_data(data, num_new_points)
    # Calculate current density and power
    current_density = 1000 * new_data['Current'] / area_cm2
    new_data['current_density'] = current_density
    new_data['Power'] = new_data['Voltage'] * new_data['current_density']
    # Find the current where voltage is zero (Isc)
    jsc_current = -current_density[new_data['Voltage'].abs().argmin()]  
    # Find the voltage where current is closest to zero (Voc)
    voc_voltage = new_data['Voltage'][current_density.abs().argmin()]
    # Find the Fill Factor
    p_max = np.min(new_data['Power'])
    fill_factor = -100 * p_max / (jsc_current * voc_voltage)
    # PCE Calculations
    pce = (jsc_current * voc_voltage * fill_factor) / input_power_mw_cm2

    return jsc_current, voc_voltage, fill_factor, pce, new_data


# Function to format the value to three digits
def format_value(val):
    return f"{val:.3f}"


# Streamlit app
def main():
  
    st.markdown(
        """
        <style>
        .header {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
        }
        .logo img {
            width: 100px;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .social-links {
            display: flex;
            justify-content: center;
            margin-top: 10px;
        }
        .social-links a {
            margin: 0 10px;
            color: #3366cc;
            font-size: 18px;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # File upload and user input
    area_mm2 = st.sidebar.number_input("Enter the active area of solar cell (in mm²):", min_value=1.00, max_value=1000.00, value=6.00, step=0.01)
    input_power_mw_cm2 = st.sidebar.number_input("Enter the input power (in mW/cm²):",  min_value=1.0, max_value=150.0, value=100.0, step=0.1)
    area_cm2 = area_mm2 / 100.0  # Convert area from mm^2 to cm^2
    st.sidebar.write("Option 1: Paste the data as two columns (Voltage (Volt) , Current (Amp)) separated by commas or tabs:")
    direct_input = st.sidebar.text_area("Direct Input", value="", height=100)
    uploaded_file = st.sidebar.file_uploader("Option 2: Upload your .csv file, Provide the full scan data (Voltage (Volt) , Current (Amp))", type=["csv"])

    data = None  # Initialize the data variable
    if uploaded_file is not None:
        # Read the uploaded data
        data = pd.read_csv(uploaded_file)
        # Automatically assign column names
        data.columns = ['Voltage', 'Current']  # You can change the column names if needed
        st.write("Data loaded successfully. Please use the light theme for better visualization")
    elif direct_input:
        # Convert direct input to a DataFrame
        data = pd.read_csv(StringIO(direct_input), sep='\t|,', engine='python', header=None)
        data.columns = ['Voltage', 'Current']
        # Convert 'Voltage' and 'Current' columns to numeric types
        data['Voltage'] = pd.to_numeric(data['Voltage'], errors='coerce')
        data['Current'] = pd.to_numeric(data['Current'], errors='coerce')
        # Drop rows with NaN values
        data.dropna(inplace=True)

    if data is not None:  # Calculate results and plot IV curve if data is loaded
        # Calculate IV curve and PCE
        jsc_current, voc_voltage, fill_factor, pce, new_data = calculate_pce(area_cm2, input_power_mw_cm2, data)
        # Create a DataFrame for the results
        results_data = pd.DataFrame({
            'Photovoltaic Parameters': ['Active Area **user input**', 'Input Power **user input', 'Short-Circuit Current Density (Jsc) mA/cm²', 'Open-Circuit Voltage (Voc) (V)', 'Fill Factor (FF) (%)', 'Power Conversion Efficiency (PCE) (%)'],
            'Value': [area_mm2, input_power_mw_cm2, jsc_current, voc_voltage, fill_factor, pce],
            'Units': ['mm²', 'mW/cm²', 'mA/cm²', 'V', '%', '%']
        })
        # Format the 'Value' column to three significant digits
        results_data['Value'] = results_data['Value'].apply(format_value)

        # Display the results in a table with units, making the values in the 'Value' column bold
        st.write("Results:")
        results_data_styled = results_data.style.apply(lambda x: ["font-weight: bold" if col == 'Value' else "" for col in x], axis=1)
        st.table(results_data_styled)     
        # Concatenate the results and the new data into a single DataFrame
        combined_data = pd.concat([results_data, new_data], ignore_index=True)
        
        # Plot the IV curve using Plotly graph_objects
        fig = go.Figure()
        # ... (rest of the code for plotting IV curve)
        # Adding IV curve line
        fig.add_trace(go.Scatter(x=new_data['Voltage'], y=new_data['current_density'], mode='lines', line=dict(color='blue', width=3), name='IV Curve'))
        fig.add_shape(type='line', x0=0, x1=0, y0=-50, y1=300, line=dict(color='black', width=1), name='Voltage = 0')
        fig.add_shape(type='line', x0=-5, x1=5, y0=0, y1=0, line=dict(color='black', width=1), name='Current = 0')
        # Adding text box with results
        fig.add_annotation(
            x=0.30,
            y=-2.0,
            text=f'PCE: {pce:.3f} %, Jsc = {jsc_current:.3f} mA/cm², Voc: {voc_voltage:.3f} V, FF : {fill_factor:.3f} %',
            showarrow=False,
            font=dict(size=16),
            bordercolor='black',
            borderwidth=1,
            borderpad=5,
            bgcolor='white'
        )
        # Adding a border around the plot
        fig.add_shape(type='rect',
                      xref='paper', yref='paper',
                      x0=0, y0=0, x1=1, y1=1,
                      line=dict(color='black', width=2))
     
        fig.update_layout(
            xaxis_title='Voltage (V)',
            yaxis_title='Current Density (mA/cm²)',
            title='Solar Cell J-V Curve',
            xaxis_range=[-0.2, 1],
            yaxis_range=[-30, 5],
            legend=dict(x=0.7, y=0.9),
            xaxis=dict(title_font=dict(size=18, family='Arial, sans-serif', color='black'), tickfont = dict(size=15, family='Arial, sans-serif', color='black')),
            yaxis=dict(title_font=dict(size=18, family='Arial, sans-serif', color='black'), tickfont = dict(size=15, family='Arial, sans-serif', color='black')),
            plot_bgcolor='white',
            hovermode='closest',
            autosize=False,
            width=700,
            height=500,
            xaxis_showgrid=True,  # Show vertical gridlines
            yaxis_showgrid=True,  # Show horizontal gridlines
            margin=dict(l=50, r=50, b=50, t=50, pad=4, autoexpand=True),
        )
        st.plotly_chart(fig)

        # Download button to save all data (results + new data) as a single CSV
        csv_combined = combined_data.to_csv(index=False)
        b64_combined = base64.b64encode(csv_combined.encode()).decode()  # Convert DataFrame to base64
        href_combined = f'<a href="data:file/csv;base64,{b64_combined}" download="J-V data and calculated parameters.csv">Download All Data (Results + J-V data)</a>'
        st.markdown(href_combined, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
