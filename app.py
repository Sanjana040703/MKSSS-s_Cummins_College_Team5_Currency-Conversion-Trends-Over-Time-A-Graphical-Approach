import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
import glob
from flask import Flask, render_template,request
import os
import csv
import io
import base64

app = Flask(__name__)

def get_unique_columns(files):
    unique_columns = set()
    for file in files:
        with open(file, 'r') as csv_file:
            reader = csv.reader(csv_file)
            columns = next(reader)  
            unique_columns.update(columns) 
    
    unique_columns.remove("Date")
    
    return list(unique_columns)  # Convert set back to a list for rendering

@app.route('/')
def index():
    # CSV files directory
    directory = r'C:\Users\HP\Desktop\Hackathon\Exchange_Rate_Report_Zip_FIle'
    files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.csv')]

    # Get unique column names from all CSV files
    column_names = get_unique_columns(files)

    # Pass column_names to the HTML template
    return render_template('index.html', column_names=column_names)

# Upload multiple CSV files
file_paths = glob.glob("*.csv") # Modify the file path pattern as needed
combined_data = pd.concat((pd.read_csv(f, index_col=0, parse_dates=['Date'], date_parser=pd.to_datetime)for f in file_paths))

# Replace missing values or NaNs if required
combined_data.fillna(method='ffill', inplace=True) # Example: Forward fill missing values

# Function to handle the selection and comparison
@app.route('/generate_graph', methods=['POST'])
def compare_currencies():
    currency1 = request.form['currency1']
    currency2 = request.form['currency2']
    duration = request.form['duration']
    
    # Fetch exchange rates for the selected currencies
    rates_currency1 = combined_data[currency1]
    rates_currency2 = combined_data[currency2]
    
    # Resample based on the selected duration
    if duration == 'weekly':
        resampled_data = combined_data.resample('W-Mon').mean()
    elif duration == 'monthly':
        resampled_data = combined_data.resample('M').mean()
    elif duration == 'quarterly':
        resampled_data = combined_data.resample('Q').mean()
    elif duration == 'annual' :
        resampled_data = combined_data.resample('Y').mean()
    
    # Calculate the conversion rate (currency1 to currency2)
    conversion_rate = resampled_data[currency2] / resampled_data[currency1]
    
    # Find the date and value for the highest rate
    highest_rate_date = conversion_rate.idxmax()
    highest_rate = conversion_rate.max()
    
    # Find the date and value for the lowest rate
    lowest_rate_date = conversion_rate.idxmin()
    lowest_rate = conversion_rate.min()
    
    # Create a figure for comparison
    fig = plt.figure(figsize=(10, 10))
    plt.plot(conversion_rate.index, conversion_rate, marker='o')
    plt.xlabel('Date')
    plt.ylabel(f'{currency1} to {currency2} Conversion Rate')
    plt.title(f'{currency1} to {currency2} Conversion Rate ({duration})')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.ylim(conversion_rate.min() - 1, conversion_rate.max() + 1)
        
    # Annotate the highest rate on the plot
    plt.annotate(f'Highest: {highest_rate:.2f}\non {highest_rate_date.strftime("%Y-%m-%d")}',
                 xy=(highest_rate_date, highest_rate),
                 xytext=(highest_rate_date, highest_rate * 1.1),
                 fontsize=9,
                 color='red',  # Set the color of the annotation text to red
                 arrowprops=dict(facecolor='red', arrowstyle='->'))
    
    # Annotate the lowest rate on the plot
    plt.annotate(f'Lowest: {lowest_rate:.2f}\non {lowest_rate_date.strftime("%Y-%m-%d")}',
                 xy=(lowest_rate_date, lowest_rate),
                 xytext=(lowest_rate_date, lowest_rate * 1.05),
                 fontsize=9,
                 color='red',  # Set the color of the annotation text to red
                 arrowprops=dict(facecolor='red', arrowstyle='->'))
        
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    
    # Encode the plot image to base64 for displaying in HTML
    graph_url = base64.b64encode(img.getvalue()).decode()
    img.close()
    
    return f'<img src="data:image/png;base64,{graph_url}">'

if __name__ == '__main__':
    app.run(debug=True)