# run_stock_requests.sh
# Run stockscrape's `headline_to_db.py` within the master branch.
# David Prager Branner
# 20140927

cd /home/dpb/github_public/stockscrape
touch _first
source /home/dpb/github_public/stockscrape/v_env3/bin/activate
touch _second
python /home/dpb/github_public/stockscrape/headline_to_db.py
touch _third
git add -A /home/dpb/github_public/stockscrape
touch _fourth
git commit -m 'upload downloads from today'
touch _ fifth

