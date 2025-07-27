from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import base64
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')
def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            return render(request, 'register.html', {'error': "Passwords do not match"})
        elif User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        else:
            user = User.objects.create_user(username=username, password=password1)
            user.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login_page')
    return render(request, 'register.html')
def logout_user(request):
    logout(request)
    return redirect('login_page')
@login_required
def home(request):
    return render(request, 'home.html')
@login_required
def result(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        try:
            df = pd.read_csv(csv_file)
            features = df[['Age', 'Annual Income (k$)', 'Family_Size', 'Work_Experience']]
            features.fillna(features.mean(numeric_only=True), inplace=True)
            if 'Spending' not in df.columns:
                np.random.seed(42)
                df['Spending'] = np.random.randint(20, 100, size=len(df))
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)
            kmeans = KMeans(n_clusters=3, random_state=42)
            labels = kmeans.fit_predict(scaled_features)
            df['Cluster'] = labels
            pca = PCA(n_components=2)
            reduced_data = pca.fit_transform(scaled_features)
            df['PCA1'], df['PCA2'] = reduced_data[:, 0], reduced_data[:, 1]
            color_mapping = {0: 'purple', 1: 'green', 2: 'orange'}
            colors = [color_mapping[label] for label in df['Cluster']]
            legend_patches = [
                mpatches.Patch(color='purple', label='Cluster 0'),
                mpatches.Patch(color='green', label='Cluster 1'),
                mpatches.Patch(color='orange', label='Cluster 2'),
            ]
            fig, ax = plt.subplots(figsize=(15, 8))
            ax.scatter(df['PCA1'], df['PCA2'], c=colors, s=60, edgecolor='black', linewidth=0.5)
            ax.set_title("Customer Segmentation using K-Means")
            ax.set_xlabel("PCA Component 1")
            ax.set_ylabel("PCA Component 2")
            ax.grid(True)
            ax.legend(handles=legend_patches, title="Cluster Colors", loc='upper right')
            buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plot_url = base64.b64encode(image_png).decode('utf-8')
            cluster_summary = df.groupby('Cluster')[['Age', 'Annual Income (k$)', 'Family_Size', 'Work_Experience', 'Spending']].mean().reset_index()
            cluster_summary = cluster_summary.round(0).astype(int)
            cluster_summary_dict = cluster_summary.to_dict(orient='records')
            gender_summary = []
            if 'Gender' not in df.columns:
                df['Gender'] = np.random.choice(['Male', 'Female'], size=len(df))
            for (cluster, gender), group in df.groupby(['Cluster', 'Gender']):
                avg_age = int(group['Age'].mean())
                if 'Frequently_Purchased_Item' in group.columns:
                    items_series = pd.Series(','.join(group['Frequently_Purchased_Item']).split(','))
                    top_items = items_series.value_counts().head(3).index.tolist()
                else:
                    top_items = "N/A"
                gender_summary.append({
                    'Cluster': cluster,
                    'Gender': gender,
                    'Avg_Age': avg_age,
                    'Top_Items': top_items
                })
            return render(request, 'result.html', {
                'plot_url': plot_url,
                'cluster_summary': cluster_summary_dict,
                'gender_summary': gender_summary,
            })
        except Exception as e:
            return render(request, 'home.html', {'error': str(e)})
    return render(request, 'home.html')
