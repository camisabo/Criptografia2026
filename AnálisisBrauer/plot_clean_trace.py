import json
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_score(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_points(score, filter_repeats=True, per_part=True):
    # Expect score to be a list of parts as produced by parse_score.py
    points = []
    for part in score:
        part_id = part.get('part', None)
        seq = 0
        for measure in part.get('measures', []):
            for ev in measure.get('notes', []):
                seq += 1
                # Skip rests (no staff_position)
                sp = ev.get('staff_position', None)
                if sp is None:
                    continue
                dur = ev.get('duration', 0.0)
                # If staff_position is a list (chord), expand into multiple points
                if isinstance(sp, list):
                    for s in sp:
                        points.append({
                            'part': part_id,
                            'x': seq,
                            'y': s,
                            'duration': dur
                        })
                else:
                    points.append({
                        'part': part_id,
                        'x': seq,
                        'y': sp,
                        'duration': dur
                    })

    if filter_repeats:
        # remove consecutive duplicates (same y and duration)
        filtered = []
        prev = None
        for p in points:
            key = (p['y'], round(p['duration'], 6))
            if prev is None or key != prev:
                filtered.append(p)
                prev = key
        points = filtered

    return points


def plot_points(points, outpath, jitter=0.08, split_per_part=False):
    if not points:
        print('No points to plot')
        return

    parts = sorted({p['part'] for p in points})
    cmap = plt.get_cmap('tab10')

    if split_per_part and len(parts) > 1:
        fig, axes = plt.subplots(len(parts), 1, sharex=True, figsize=(10, 2*len(parts)))
        if len(parts) == 1:
            axes = [axes]
        for idx, part in enumerate(parts):
            ax = axes[idx]
            part_points = [p for p in points if p['part'] == part]
            xs = np.array([p['x'] for p in part_points])
            ys = np.array([p['y'] for p in part_points])
            rng = np.random.default_rng(part if isinstance(part, int) else idx)
            xs = xs + rng.normal(0, jitter, size=xs.shape)
            ax.scatter(xs, ys, s=10, alpha=0.85, color=cmap(idx % 10))
            ax.set_ylabel(f'Part {part}')
            ax.grid(alpha=0.3)
        axes[-1].set_xlabel('Sequence index')
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        for idx, part in enumerate(parts):
            part_points = [p for p in points if p['part'] == part]
            xs = np.array([p['x'] for p in part_points])
            ys = np.array([p['y'] for p in part_points])
            rng = np.random.default_rng(part if isinstance(part, int) else idx)
            xs = xs + rng.normal(0, jitter, size=xs.shape)
            ax.scatter(xs, ys, s=12, alpha=0.75, color=cmap(idx % 10), label=f'Part {part}')
        ax.set_xlabel('Sequence index')
        ax.set_ylabel('Staff position (diatonic distance)')
        ax.grid(alpha=0.25)
        if len(parts) > 1:
            ax.legend(markerscale=2)

    plt.tight_layout()
    fig.savefig(outpath, dpi=200)
    plt.close(fig)
    print(f'Plot saved to {outpath}')


def main():
    parser = argparse.ArgumentParser(description='Plot clean trace from score JSON')
    parser.add_argument('json', help='Score JSON path')
    parser.add_argument('--out', '-o', default='graph_clean.png', help='Output PNG path')
    parser.add_argument('--no-filter', dest='filter', action='store_false', help='Disable repeat filtering')
    parser.add_argument('--split-per-part', action='store_true', help='Split plot per part')
    args = parser.parse_args()

    score = load_score(args.json)
    points = build_points(score, filter_repeats=args.filter)
    plot_points(points, args.out, split_per_part=args.split_per_part)


if __name__ == '__main__':
    main()
