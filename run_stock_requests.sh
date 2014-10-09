# run_stock_requests.sh
# Run stockscrape's `headline_to_db.py` within the master branch.
# David Prager Branner
# 20141009

cd /home/dpb/github_public/stockscrape
source /home/dpb/github_public/stockscrape/v_env3/bin/activate
python /home/dpb/github_public/stockscrape/headline_to_db.py
git add -A /home/dpb/github_public/stockscrape
git commit -m 'upload downloads from today'

