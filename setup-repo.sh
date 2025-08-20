#!/bin/bash

# After creating a new repository on GitHub, run this script
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username

echo "Enter your GitHub username:"
read GITHUB_USERNAME

git remote add origin "https://github.com/${GITHUB_USERNAME}/matchbot_ai.git"
git branch -M master
git push -u origin master

echo "Repository setup complete!"