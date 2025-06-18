from flask import Flask, request, jsonify
from flask_cors import CORS
from TikTokApi import TikTokApi
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

def compute_virality(video):
    views = video.stats.play_count
    likes = video.stats.digg_count
    comments = video.stats.comment_count
    engagement = (likes + comments) / max(views, 1)
    return views * engagement

@app.route('/videos', methods=['GET'])
def get_videos():
    country = request.args.get('country', '').strip()
    MIN_VIEWS = 30000  # minimum view count filter

    if not country:
        return jsonify({"error": "Please specify ?country="}), 400

    query = f"{country}"
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    results = []

    # List of categories/keywords to filter in description
    categories = ['funny', 'fight', 'comedy', 'unbelievable', 'danger']

    with TikTokApi() as api:
        for video in api.search.videos(query=query, count=50):
            stats = video.stats
            views = stats.play_count
            ts = datetime.fromtimestamp(video.create_time)
            if ts < two_days_ago:
                continue

            if views < MIN_VIEWS:
                continue

            desc = video.desc.lower()
            # Check if any category keyword is in description
            if not any(cat in desc for cat in categories):
                continue

            virality = compute_virality(video)
            vid = {
                "id": video.id,
                "title": video.desc[:50],
                "author": video.author.username,
                "url": f"https://www.tiktok.com/@{video.author.username}/video/{video.id}",
                "thumbnail": video.video.cover,
                "views": stats.play_count,
                "likes": stats.digg_count,
                "comments": stats.comment_count,
                "shares": getattr(stats, 'share_count', None),
                "engagement": round((stats.digg_count + stats.comment_count) / max(stats.play_count, 1), 3),
                "sound": video.music.title if video.music else None,
                "published": ts.isoformat(),
                "virality_score": round(virality, 2)
            }
            results.append(vid)

    results.sort(key=lambda x: x['virality_score'], reverse=True)
    return jsonify(results[:20])

if __name__ == '__main__':
    app.run(debug=True)
