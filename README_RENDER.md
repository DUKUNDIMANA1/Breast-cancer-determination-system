# BreastCare AI - Render Deployment Guide

## 🚀 Deploy to Render

This guide will help you deploy your BreastCare AI application to Render.com for production hosting.

### 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push your code to GitHub
3. **MongoDB Atlas**: Ensure database is accessible
4. **Environment Variables**: Configure all required variables

### 🔧 Environment Variables

Set these in your Render dashboard:

#### Database Configuration
- `MONGO_URI`: Your MongoDB Atlas connection string
- `MONGO_DB_NAME`: `breastcare_ai`

#### Application Configuration
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_ENV`: `production`

#### Email Configuration (Optional)
- `EMAIL_SERVER`: `smtp.gmail.com`
- `EMAIL_PORT`: `587`
- `EMAIL_USERNAME`: Your Gmail address
- `EMAIL_PASSWORD`: Your Gmail app password

### 🚀 Deployment Steps

#### 1. Connect Repository
```bash
# Install Render CLI
npm install -g render

# Login to Render
render login

# Connect your repository
render connect https://github.com/yourusername/breast-cancer-determination-system
```

#### 2. Deploy Application
```bash
# Create web service
render create web-service

# Choose settings:
# - Name: breastcare-ai
# - Region: Oregon (or nearest to you)
# - Plan: Free (to start)
```

#### 3. Configure Environment
```bash
# Set environment variables in Render dashboard
# Go to your service → Settings → Environment
# Add all required variables from above
```

#### 4. Deploy
```bash
# Deploy your application
render push
```

### 🌐 Access Your Application

Once deployed, your app will be available at:
- **URL**: `https://breastcare-ai.onrender.com`
- **Admin**: Access at `/admin` for admin dashboard
- **API**: All endpoints available

### 🔧 Production Considerations

#### Database
- **MongoDB Atlas**: Ensure IP whitelist includes Render's IP
- **Connection**: Use connection string with retry logic
- **Backup**: Regular database backups recommended

#### Security
- **HTTPS**: Automatic SSL certificate from Render
- **Environment**: Never expose secrets in code
- **Rate Limiting**: Consider implementing for API endpoints

#### Performance
- **Free Plan**: Limited to 750 hours/month
- **Scaling**: Auto-scaling available on paid plans
- **Monitoring**: Built-in metrics dashboard

### 🛠️ Troubleshooting

#### Common Issues
1. **Database Connection**: Check MongoDB URI and IP whitelist
2. **Build Errors**: Verify requirements.txt has all dependencies
3. **Environment Variables**: Ensure all required variables are set
4. **Port Issues**: Application runs on port 5000 internally

#### Debug Commands
```bash
# Check deployment logs
render logs breastcare-ai

# Access application shell
render shell breastcare-ai

# Restart service
render restart breastcare-ai
```

### 📊 Monitoring

#### Render Dashboard
- **Metrics**: CPU, memory, and usage statistics
- **Logs**: Real-time application logs
- **Alerts**: Email notifications for issues
- **Backups**: Automatic snapshots

### 🔄 Updates

#### Deploying Updates
```bash
# Push changes to GitHub
git add .
git commit -m "Update features"
git push origin main

# Redeploy on Render
render deploy
```

### 📞 Support

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Community Forum**: [community.render.com](https://community.render.com)
- **Status Page**: [status.render.com](https://status.render.com)

---

**🎉 Your BreastCare AI application is now ready for production deployment on Render!**
