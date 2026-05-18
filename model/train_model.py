import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import pickle
import os

def train_expense_model():
    """Train a simple expense prediction model."""
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../dataset/expenses.csv'))
    
    le = LabelEncoder()
    df['category_encoded'] = le.fit_transform(df['category'])
    
    X = df[['month', 'category_encoded']]
    y = df['amount']
    
    model = LinearRegression()
    model.fit(X, y)
    
    model_path = os.path.join(os.path.dirname(__file__), 'expense_model.pkl')
    encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(encoder_path, 'wb') as f:
        pickle.dump(le, f)
    
    return model, le

def load_model():
    model_path = os.path.join(os.path.dirname(__file__), 'expense_model.pkl')
    encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.pkl')
    
    if not os.path.exists(model_path):
        return train_expense_model()
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(encoder_path, 'rb') as f:
        le = pickle.load(f)
    
    return model, le

def predict_expense(month, category):
    model, le = load_model()
    try:
        cat_encoded = le.transform([category])[0]
    except ValueError:
        cat_encoded = 0
    
    prediction = model.predict([[month, cat_encoded]])[0]
    return max(0, round(prediction, 2))

def analyze_spending(expenses_data):
    """Analyze spending patterns and return insights."""
    if not expenses_data:
        return {
            'total': 0,
            'avg_daily': 0,
            'top_category': 'N/A',
            'trend': 'neutral',
            'suggestions': ['Start adding expenses to get personalized insights!']
        }
    
    df = pd.DataFrame(expenses_data)
    
    total = df['amount'].sum()
    avg_daily = total / 30
    top_category = df.groupby('category')['amount'].sum().idxmax() if len(df) > 0 else 'N/A'
    
    suggestions = []
    category_totals = df.groupby('category')['amount'].sum()
    
    if 'Food' in category_totals and category_totals['Food'] > 6000:
        suggestions.append('Your Food expenses are high. Try meal prepping to save ₹500–₹1000/month.')
    if 'Entertainment' in category_totals and category_totals['Entertainment'] > 2000:
        suggestions.append('Consider reviewing subscription services to cut Entertainment costs.')
    if 'Shopping' in category_totals and category_totals['Shopping'] > 5000:
        suggestions.append('Shopping spending is elevated. Try a 24-hour rule before purchases.')
    if total > 20000:
        suggestions.append('Total spending is high. Consider setting a monthly budget of ₹18,000.')
    if not suggestions:
        suggestions.append('Great job! Your spending looks balanced this month.')
    
    return {
        'total': round(total, 2),
        'avg_daily': round(avg_daily, 2),
        'top_category': top_category,
        'suggestions': suggestions
    }

if __name__ == '__main__':
    print("Training model...")
    train_expense_model()
    print("Model trained successfully!")
    print(f"Prediction for month 7, Food: ₹{predict_expense(7, 'Food')}")
