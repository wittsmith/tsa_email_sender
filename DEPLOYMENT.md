# Cloud Deployment Guide - Railway

## Quick Setup (5 minutes)

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub (free)

### 2. Deploy Your Project
1. **Click "New Project"**
2. **Select "Deploy from GitHub repo"**
3. **Choose your TSA repository**
4. **Railway will automatically detect it's a Python project**

### 3. Set Environment Variables
In Railway dashboard, go to your project → Variables tab and add:

```
SENDER_EMAIL=your_gmail@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@example.com
```

### 4. Deploy
- Railway will automatically build and deploy
- Your script will start running immediately
- Check the logs to see it working

## What Happens Next

✅ **Your script runs 24/7** on Railway's servers  
✅ **Automatically restarts** if it crashes  
✅ **Runs at 9:05 AM ET** every weekday regardless of your computer  
✅ **Sends emails** with TSA data and visualizations  
✅ **Free tier** includes 500 hours/month (plenty for this use case)  

## Monitoring

- **Logs**: View real-time logs in Railway dashboard
- **Status**: See if your script is running
- **Restarts**: Automatic if the script fails

## Cost

- **Free tier**: 500 hours/month (enough for 24/7 operation)
- **Paid**: $5/month if you exceed free tier

## Alternative: Render

If Railway doesn't work, try [render.com](https://render.com):
1. Same process, just different platform
2. Also has free tier
3. Slightly different configuration

## Troubleshooting

**Script not starting?**
- Check Railway logs
- Verify environment variables are set
- Make sure all dependencies are in requirements.txt

**Emails not sending?**
- Verify Gmail app password is correct
- Check Railway logs for email errors
- Ensure recipient email is correct 