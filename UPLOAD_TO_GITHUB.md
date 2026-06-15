# Upload to GitHub

Run these commands inside this `github_release` folder.

First, re-authenticate GitHub CLI if needed:

```powershell
gh auth login -h github.com
```

Then initialize Git:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial final project release"
```

Create a new repository on GitHub, then connect it:

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/multi-model-boundary-refinement-person-segmentation.git
git push -u origin main
```

After pushing, the project link will be:

```text
https://github.com/YOUR_ACCOUNT/multi-model-boundary-refinement-person-segmentation
```
