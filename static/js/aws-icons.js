/** AWS icon search + HLD diagram rendering (aws_icons/png-512) */
(function() {
    var manifestPromise = null;
    var ICON_SIZE = 72;
    var LABEL_GAP = 20;
    var LABEL_HEIGHT = 40;
    var annotationStore = {};
    var annotationPersistTimers = {};

    function normalize(text) {
        return String(text || '').toLowerCase()
            .replace(/\b(amazon|aws)\b/g, ' ')
            .replace(/[^a-z0-9]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function compact(text) {
        return normalize(text).replace(/\s+/g, '');
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scoreLabelAgainstIcon(labelNorm, labelCompact, icon) {
        var score = 0;
        var nameNorm = normalize(icon.name);
        var nameCompact = compact(icon.name);

        if (labelCompact && nameCompact && labelCompact === nameCompact) return 1000;
        if (labelNorm && nameNorm && labelNorm === nameNorm) return 950;
        if (nameCompact && labelCompact.indexOf(nameCompact) !== -1) {
            score = Math.max(score, 800 + nameCompact.length);
        }
        if (nameNorm && labelNorm.indexOf(nameNorm) !== -1) {
            score = Math.max(score, 700 + nameNorm.length);
        }

        var tokens = icon.tokens || [];
        for (var i = 0; i < tokens.length; i++) {
            var tNorm = normalize(tokens[i]);
            var tCompact = compact(tokens[i]);
            if (tCompact.length < 3) continue;
            if (tCompact === labelCompact) score = Math.max(score, 900);
            else if (labelCompact.indexOf(tCompact) !== -1) score = Math.max(score, 500 + tCompact.length);
            else if (tNorm && labelNorm.indexOf(tNorm) !== -1) score = Math.max(score, 400 + tNorm.length);
        }

        var labelWords = labelNorm.split(' ');
        var nameWords = nameNorm.split(' ');
        var overlap = 0;
        for (var j = 0; j < labelWords.length; j++) {
            for (var k = 0; k < nameWords.length; k++) {
                if (labelWords[j] && labelWords[j] === nameWords[k]) overlap++;
            }
        }
        if (overlap) score = Math.max(score, 300 + 50 * overlap);

        return score;
    }

    function buildFilenameIndex(icons) {
        var byFile = {};
        for (var i = 0; i < icons.length; i++) {
            var icon = icons[i];
            var base = (icon.file || '').replace(/\.png$/i, '');
            byFile[base.toLowerCase()] = icon;
            byFile[compact(base)] = icon;
        }
        return byFile;
    }

    function resolveAliasTarget(aliasTarget, byFile) {
        if (!aliasTarget || !byFile) return null;
        var aliasKey = aliasTarget.toLowerCase();
        if (byFile[aliasKey]) return byFile[aliasKey].path;
        var aliasCompact = compact(aliasTarget);
        if (byFile[aliasCompact]) return byFile[aliasCompact].path;
        return null;
    }

    window.loadAwsIconManifest = function() {
        if (window.AWS_ICON_MANIFEST) {
            return Promise.resolve(window.AWS_ICON_MANIFEST);
        }
        if (!manifestPromise) {
            manifestPromise = fetch('/api/aws-icons/manifest')
                .then(function(res) {
                    if (!res.ok) throw new Error('Failed to load AWS icon manifest');
                    return res.json();
                })
                .then(function(data) {
                    window.AWS_ICON_MANIFEST = data;
                    window.AWS_ICON_BY_FILE = buildFilenameIndex(data.icons || []);
                    return data;
                })
                .catch(function(err) {
                    console.warn('AWS icon manifest load failed:', err);
                    window.AWS_ICON_MANIFEST = { icons: [], aliases: {} };
                    window.AWS_ICON_BY_FILE = {};
                    return window.AWS_ICON_MANIFEST;
                });
        }
        return manifestPromise;
    };

    window.matchAwsIcon = function(labelText) {
        var manifest = window.AWS_ICON_MANIFEST;
        if (!manifest || !manifest.icons || !manifest.icons.length) return null;

        var labelNorm = normalize(labelText);
        var labelCompact = compact(labelText);
        if (!labelNorm) return null;

        var aliases = manifest.aliases || {};
        var byFile = window.AWS_ICON_BY_FILE || {};

        if (aliases[labelCompact]) {
            var exact = resolveAliasTarget(aliases[labelCompact], byFile);
            if (exact) return exact;
        }
        if (aliases[labelNorm]) {
            var exactNorm = resolveAliasTarget(aliases[labelNorm], byFile);
            if (exactNorm) return exactNorm;
        }

        var bestAlias = null;
        var bestAliasLen = 0;
        for (var alias in aliases) {
            if (!Object.prototype.hasOwnProperty.call(aliases, alias)) continue;
            var aliasNorm = normalize(alias);
            if (labelNorm.indexOf(aliasNorm) !== -1 && aliasNorm.length > bestAliasLen) {
                bestAlias = aliases[alias];
                bestAliasLen = aliasNorm.length;
            }
        }
        if (bestAlias) {
            var aliasPath = resolveAliasTarget(bestAlias, byFile);
            if (aliasPath) return aliasPath;
        }

        var best = null;
        var bestScore = 0;
        var icons = manifest.icons;
        for (var i = 0; i < icons.length; i++) {
            var score = scoreLabelAgainstIcon(labelNorm, labelCompact, icons[i]);
            if (score > bestScore) {
                bestScore = score;
                best = icons[i];
            }
        }

        return (best && bestScore >= 300) ? best.path : null;
    };

    function getNodeLabelText(nodeGroup) {
        var labelEl = nodeGroup.querySelector('.nodeLabel')
            || nodeGroup.querySelector('foreignObject div')
            || nodeGroup.querySelector('g.label span')
            || nodeGroup.querySelector('g.label')
            || nodeGroup.querySelector('text');
        var text = labelEl ? String(labelEl.textContent || '').trim() : '';
        if (!text) {
            var id = nodeGroup.id || '';
            var match = id.match(/flowchart-([^-]+)/i);
            if (match && match[1]) {
                text = match[1].replace(/_/g, ' ').trim();
            } else {
                text = id.replace(/^flowchart-/i, '').replace(/-/g, ' ').trim() || 'Component';
            }
        }
        return text;
    }

    function parseNodeLabel(text) {
        var raw = String(text || '').trim();
        var isBottleneck = /\[\s*bottleneck\s*\]/i.test(raw) || /\bbottleneck\b/i.test(raw);
        var clean = raw
            .replace(/\u00a0/g, ' ')
            .replace(/\s*\[\s*bottleneck\s*\]\s*/gi, ' ')
            .replace(/\s*-\s*bottleneck\s*/gi, ' ')
            .replace(/\bbottleneck\b/gi, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        return { raw: raw, clean: clean || raw, isBottleneck: isBottleneck };
    }

    function detectMermaidShape(nodeGroup) {
        if (!nodeGroup) return null;
        if (nodeGroup.querySelector('polygon')) return 'diamond';
        if (nodeGroup.querySelector('circle')) return 'circle';
        var paths = nodeGroup.querySelectorAll('path');
        for (var i = 0; i < paths.length; i++) {
            if (paths[i].closest('.edgePath')) continue;
            var d = paths[i].getAttribute('d') || '';
            if (/[Aa]/.test(d) && paths[i].getAttribute('fill') !== 'none') return 'cylinder';
        }
        var ellipses = nodeGroup.querySelectorAll('ellipse');
        if (ellipses.length >= 2 && nodeGroup.querySelector('rect')) return 'cylinder';
        if (ellipses.length === 1 && !nodeGroup.querySelector('rect')) return 'circle';
        return 'rect';
    }

    function inferNodeShape(text) {
        var n = normalize(text);
        if (/wal|sstable|ss table|database|disk|storage|store|table|log|file|s3|rds|postgres|dynamo|persist|segment/.test(n)) {
            return 'cylinder';
        }
        if (/memtable|cache|memory|buffer|client|user|session|redis/.test(n)) {
            return 'circle';
        }
        if (/filter|bloom|decision|router|split|guard|validat|branch/.test(n)) {
            return 'diamond';
        }
        if (/queue|kafka|stream|bus|event|topic|pub|sub|pipe/.test(n)) {
            return 'hexagon';
        }
        return 'rect';
    }

    function resolveNodeShape(nodeGroup, text) {
        return detectMermaidShape(nodeGroup) || inferNodeShape(text);
    }

    function measureFallbackBox(text, shape) {
        var len = (text || '').length;
        var w = Math.min(220, Math.max(100, len * 6.8 + 36));
        var h = len > 24 ? 92 : 80;
        if (shape === 'circle') {
            var size = Math.max(w, h);
            return { w: size, h: size };
        }
        if (shape === 'diamond') {
            return { w: w + 28, h: h + 28 };
        }
        if (shape === 'hexagon') {
            return { w: w + 16, h: h + 8 };
        }
        return { w: w, h: h };
    }

    function createBottleneckBadge(cx, bodyTopY, bodySize) {
        var badgeW = 118;
        var badgeH = 20;
        var fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
        fo.setAttribute('class', 'aws-bottleneck-badge-wrap');
        fo.setAttribute('x', String(cx - badgeW / 2));
        fo.setAttribute('y', String(bodyTopY + bodySize + 6));
        fo.setAttribute('width', String(badgeW));
        fo.setAttribute('height', String(badgeH));
        fo.innerHTML = '<div xmlns="http://www.w3.org/1999/xhtml" class="aws-bottleneck-badge">Scale bottleneck</div>';
        return fo;
    }

    function hideNodeShapes(nodeGroup) {
        nodeGroup.querySelectorAll('rect, circle, polygon, ellipse, path').forEach(function(shape) {
            if (shape.closest('.edgePath') || shape.classList.contains('aws-service-icon')) return;
            if (shape.closest('.aws-fallback-node')) return;
            shape.setAttribute('fill', 'none');
            shape.setAttribute('stroke', 'none');
            shape.style.opacity = '0';
        });
        nodeGroup.querySelectorAll('.label, foreignObject, .nodeLabel').forEach(function(labelPart) {
            if (labelPart.closest('.aws-icon-node') || labelPart.closest('.aws-fallback-node')) return;
            labelPart.style.opacity = '0';
            labelPart.style.pointerEvents = 'none';
        });
    }

    function measureLabelWidth(text) {
        return Math.min(220, Math.max(104, text.length * 7.5 + 36));
    }

    function createAwsLabel(cx, labelTop, text, labelWidth, labelHeight) {
        labelWidth = labelWidth || measureLabelWidth(text);
        labelHeight = labelHeight || LABEL_HEIGHT;
        var fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
        fo.setAttribute('class', 'aws-node-label-wrap aws-node-label-above');
        fo.setAttribute('x', String(cx - labelWidth / 2));
        fo.setAttribute('y', String(labelTop));
        fo.setAttribute('width', String(labelWidth));
        fo.setAttribute('height', String(labelHeight));
        fo.innerHTML = '<div xmlns="http://www.w3.org/1999/xhtml" class="aws-node-label-html">' + escapeHtml(text) + '</div>';
        return fo;
    }

    function createInlineLabel(cx, cy, w, h, text) {
        var fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
        fo.setAttribute('class', 'aws-node-label-wrap aws-node-label-inside');
        fo.setAttribute('x', String(cx - w / 2));
        fo.setAttribute('y', String(cy - h / 2));
        fo.setAttribute('width', String(w));
        fo.setAttribute('height', String(h));
        fo.innerHTML = '<div xmlns="http://www.w3.org/1999/xhtml" class="aws-node-label-html aws-node-label-html-inside">' + escapeHtml(text) + '</div>';
        return fo;
    }

    var SCALE_REPLICA_COUNT = 3;
    var SCALE_ICON_SIZE = 44;
    var SCALE_ICON_GAP = 8;
    var SCALE_BOX_PAD = 12;

    function layoutIconNode(bbox, bodySize, isBottleneck) {
        var labelHeight = LABEL_HEIGHT;
        var badgeH = isBottleneck ? 22 : 0;
        var badgeGap = isBottleneck ? 10 : 0;
        var totalH = labelHeight + LABEL_GAP + bodySize + badgeGap + badgeH;
        var stackTop = bbox.y + Math.max(14, (bbox.height - totalH) / 2);
        return {
            cx: bbox.x + bbox.width / 2,
            labelTop: stackTop,
            bodyTopY: stackTop + labelHeight + LABEL_GAP,
            labelHeight: labelHeight
        };
    }

    function scaledBoxHeight(iconSize) {
        return SCALE_REPLICA_COUNT * iconSize + (SCALE_REPLICA_COUNT - 1) * SCALE_ICON_GAP + SCALE_BOX_PAD * 2;
    }

    function layoutScaledIconNode(bbox, isBottleneck) {
        var boxH = scaledBoxHeight(SCALE_ICON_SIZE);
        var labelHeight = LABEL_HEIGHT;
        var badgeH = isBottleneck ? 22 : 0;
        var badgeGap = isBottleneck ? 10 : 0;
        var totalH = labelHeight + LABEL_GAP + boxH + badgeGap + badgeH;
        var stackTop = bbox.y + Math.max(14, (bbox.height - totalH) / 2);
        return {
            cx: bbox.x + bbox.width / 2,
            labelTop: stackTop,
            bodyTopY: stackTop + labelHeight + LABEL_GAP,
            boxH: boxH,
            labelHeight: labelHeight
        };
    }

    function createScaleBoundary(cx, topY, width, height) {
        var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('class', 'aws-scale-bounds');
        rect.setAttribute('x', String(cx - width / 2));
        rect.setAttribute('y', String(topY));
        rect.setAttribute('width', String(width));
        rect.setAttribute('height', String(height));
        rect.setAttribute('rx', '12');
        rect.setAttribute('ry', '12');
        return rect;
    }

    function replicaUnitLabel(text) {
        var t = text.replace(/\s*\[Bottleneck\]\s*/gi, '').trim();
        t = t.replace(/\b(horizontally\s+scalable|horizontal(?:ly)?\s+scal(?:e|ed|ing)|auto-?scal(?:e|ed|ing)|autoscal(?:e|ed|ing))\b/gi, '').trim();
        if (/workers?$/i.test(t)) {
            return t.replace(/workers$/i, 'Worker').replace(/worker$/i, 'Worker') || 'Worker';
        }
        if (/services?$/i.test(t)) {
            return t.replace(/services$/i, 'Service').replace(/service$/i, 'Service') || 'Service';
        }
        if (/replicas?$/i.test(t)) {
            return t.replace(/replicas$/i, 'Replica').replace(/replica$/i, 'Replica') || 'Replica';
        }
        if (/pods?$/i.test(t)) {
            return t.replace(/pods$/i, 'Pod').replace(/pod$/i, 'Pod') || 'Pod';
        }
        if (/instances?$/i.test(t)) {
            return t.replace(/instances$/i, 'Instance').replace(/instance$/i, 'Instance') || 'Instance';
        }
        var parts = t.split(/\s+/).filter(Boolean);
        return parts.length ? parts[parts.length - 1] : 'Instance';
    }

    function appendShapeBody(group, cx, cy, w, h, shape) {
        var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'aws-shape-body aws-shape-' + shape);

        var fill = '#f8fafc';
        var stroke = '#94a3b8';
        var hitPad = 4;

        if (shape === 'circle') {
            var r = Math.min(w, h) / 2;
            var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('class', 'aws-fallback-shape');
            circle.setAttribute('cx', String(cx));
            circle.setAttribute('cy', String(cy));
            circle.setAttribute('r', String(r));
            circle.setAttribute('fill', fill);
            circle.setAttribute('stroke', stroke);
            g.appendChild(circle);
            var hit = circle.cloneNode();
            hit.setAttribute('class', 'aws-shape-hit');
            hit.setAttribute('r', String(r + hitPad));
            hit.setAttribute('fill', 'transparent');
            hit.setAttribute('stroke', 'none');
            g.appendChild(hit);
        } else if (shape === 'diamond') {
            var hw = w / 2;
            var hh = h / 2;
            var points = cx + ', ' + (cy - hh) + ' ' + (cx + hw) + ', ' + cy + ' ' + cx + ', ' + (cy + hh) + ' ' + (cx - hw) + ', ' + cy;
            var poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            poly.setAttribute('class', 'aws-fallback-shape');
            poly.setAttribute('points', points);
            poly.setAttribute('fill', fill);
            poly.setAttribute('stroke', stroke);
            g.appendChild(poly);
        } else if (shape === 'hexagon') {
            var hx = w / 2;
            var hy = h / 2;
            var hex = [
                [cx - hx * 0.5, cy - hy],
                [cx + hx * 0.5, cy - hy],
                [cx + hx, cy],
                [cx + hx * 0.5, cy + hy],
                [cx - hx * 0.5, cy + hy],
                [cx - hx, cy]
            ];
            var hexPoints = hex.map(function(p) { return p[0] + ', ' + p[1]; }).join(' ');
            var hexPoly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            hexPoly.setAttribute('class', 'aws-fallback-shape');
            hexPoly.setAttribute('points', hexPoints);
            hexPoly.setAttribute('fill', fill);
            hexPoly.setAttribute('stroke', stroke);
            g.appendChild(hexPoly);
        } else if (shape === 'cylinder') {
            var topY = cy - h / 2 + 10;
            var bodyH = h - 20;
            var rx = w / 2;
            var ry = 10;
            var top = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            top.setAttribute('class', 'aws-fallback-shape');
            top.setAttribute('cx', String(cx));
            top.setAttribute('cy', String(topY));
            top.setAttribute('rx', String(rx));
            top.setAttribute('ry', String(ry));
            top.setAttribute('fill', fill);
            top.setAttribute('stroke', stroke);
            var body = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            body.setAttribute('class', 'aws-fallback-shape');
            body.setAttribute('x', String(cx - rx));
            body.setAttribute('y', String(topY));
            body.setAttribute('width', String(w));
            body.setAttribute('height', String(bodyH));
            body.setAttribute('fill', fill);
            body.setAttribute('stroke', stroke);
            var bottom = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            bottom.setAttribute('class', 'aws-fallback-shape');
            bottom.setAttribute('cx', String(cx));
            bottom.setAttribute('cy', String(topY + bodyH));
            bottom.setAttribute('rx', String(rx));
            bottom.setAttribute('ry', String(ry));
            bottom.setAttribute('fill', fill);
            bottom.setAttribute('stroke', stroke);
            g.appendChild(body);
            g.appendChild(top);
            g.appendChild(bottom);
            var hitRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            hitRect.setAttribute('class', 'aws-shape-hit');
            hitRect.setAttribute('x', String(cx - rx - hitPad));
            hitRect.setAttribute('y', String(topY - hitPad));
            hitRect.setAttribute('width', String(w + hitPad * 2));
            hitRect.setAttribute('height', String(bodyH + ry * 2 + hitPad * 2));
            hitRect.setAttribute('fill', 'transparent');
            hitRect.setAttribute('stroke', 'none');
            g.appendChild(hitRect);
        } else {
            var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('class', 'aws-fallback-shape');
            rect.setAttribute('x', String(cx - w / 2));
            rect.setAttribute('y', String(cy - h / 2));
            rect.setAttribute('width', String(w));
            rect.setAttribute('height', String(h));
            rect.setAttribute('rx', '14');
            rect.setAttribute('ry', '14');
            rect.setAttribute('fill', fill);
            rect.setAttribute('stroke', stroke);
            g.appendChild(rect);
            var hitR = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            hitR.setAttribute('class', 'aws-shape-hit');
            hitR.setAttribute('x', String(cx - w / 2 - hitPad));
            hitR.setAttribute('y', String(cy - h / 2 - hitPad));
            hitR.setAttribute('width', String(w + hitPad * 2));
            hitR.setAttribute('height', String(h + hitPad * 2));
            hitR.setAttribute('fill', 'transparent');
            hitR.setAttribute('stroke', 'none');
            g.appendChild(hitR);
        }

        group.appendChild(g);
    }

    function createFallbackNode(cx, cy, text, shape, isBottleneck) {
        var dims = measureFallbackBox(text, shape);
        var group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'aws-fallback-node aws-fallback-node-' + shape + (isBottleneck ? ' aws-icon-node-bottleneck' : ''));

        appendShapeBody(group, cx, cy, dims.w, dims.h, shape);

        var labelW = shape === 'diamond' ? dims.w * 0.55 : dims.w * 0.88;
        var labelH = shape === 'diamond' ? dims.h * 0.45 : dims.h * 0.85;
        group.appendChild(createInlineLabel(cx, cy, labelW, labelH, text));

        if (isBottleneck) {
            group.appendChild(createBottleneckBadge(cx, cy + dims.h / 2, 0));
        }

        return group;
    }

    function createScaledFallbackNode(cx, bodyTopY, text, shape, isBottleneck) {
        var unit = replicaUnitLabel(text);
        var miniW = 104;
        var miniH = 30;
        var gap = 6;
        var boxW = miniW + SCALE_BOX_PAD * 2;
        var boxH = SCALE_REPLICA_COUNT * miniH + (SCALE_REPLICA_COUNT - 1) * gap + SCALE_BOX_PAD * 2;

        var group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'aws-fallback-node aws-fallback-node-scaled aws-fallback-node-' + shape + (isBottleneck ? ' aws-icon-node-bottleneck' : ''));

        group.appendChild(createScaleBoundary(cx, bodyTopY, boxW, boxH));

        for (var i = 0; i < SCALE_REPLICA_COUNT; i++) {
            var cy = bodyTopY + SCALE_BOX_PAD + miniH / 2 + i * (miniH + gap);
            appendShapeBody(group, cx, cy, miniW, miniH, 'rect');
            group.appendChild(createInlineLabel(cx, cy, miniW * 0.9, miniH * 0.85, unit));
        }

        if (isBottleneck) {
            group.appendChild(createBottleneckBadge(cx, bodyTopY + boxH, 0));
        }

        return group;
    }

    function setImageHref(img, path) {
        img.setAttribute('href', path);
        img.setAttributeNS('http://www.w3.org/1999/xlink', 'href', path);
    }

    function isHorizontallyScaledNode(nodeGroup, text) {
        var norm = normalize(text);
        if (/horizontally scalable|horizontal scale|horizontal scaling|horizontally scaled|auto scale|autoscaling|autoscaled|hpa|replica set|scaled service|scaled worker|scaled tier|worker pool|service pool|multiple instance/.test(norm)) {
            return true;
        }
        var cluster = nodeGroup.closest('g.cluster');
        if (cluster) {
            var clusterLabel = cluster.querySelector('.cluster-label');
            var clusterText = clusterLabel ? normalize(clusterLabel.textContent || '') : '';
            if (/ecs|eks|cluster|fargate|kubernetes|container|microservice|worker|pod|service|scalable|scale/.test(clusterText)) {
                return true;
            }
        }
        if (/services|microservices|workers|replicas|tasks|instances|pods|backend|workloads/.test(norm)) {
            return true;
        }
        if (/ecs|eks|fargate|kubernetes|k8s/.test(norm) && /service|task|workload|worker|pod/.test(norm)) {
            return true;
        }
        return false;
    }

    function appendIconGraphics(layer, cx, bodyTopY, iconPath, scaled) {
        if (!scaled) {
            var img = document.createElementNS('http://www.w3.org/2000/svg', 'image');
            img.setAttribute('class', 'aws-service-icon');
            setImageHref(img, iconPath);
            img.setAttribute('width', String(ICON_SIZE));
            img.setAttribute('height', String(ICON_SIZE));
            img.setAttribute('x', String(cx - ICON_SIZE / 2));
            img.setAttribute('y', String(bodyTopY));
            layer.appendChild(img);
            return;
        }

        var size = SCALE_ICON_SIZE;
        var boxW = size + SCALE_BOX_PAD * 2 + 16;
        var boxH = scaledBoxHeight(size);

        layer.appendChild(createScaleBoundary(cx, bodyTopY, boxW, boxH));

        for (var i = 0; i < SCALE_REPLICA_COUNT; i++) {
            var iy = bodyTopY + SCALE_BOX_PAD + i * (size + SCALE_ICON_GAP);
            var ix = cx - size / 2;

            var replica = document.createElementNS('http://www.w3.org/2000/svg', 'image');
            replica.setAttribute('class', 'aws-service-icon aws-service-icon-scaled');
            setImageHref(replica, iconPath);
            replica.setAttribute('width', String(size));
            replica.setAttribute('height', String(size));
            replica.setAttribute('x', String(ix));
            replica.setAttribute('y', String(iy));
            replica.style.opacity = i === 1 ? '1' : '0.88';
            layer.appendChild(replica);
        }
    }

    window.applyAwsIconsToSvg = function(svgEl) {
        if (!svgEl || !window.matchAwsIcon) return;

        svgEl.querySelectorAll('g.node').forEach(function(nodeGroup) {
            if (nodeGroup.querySelector('g.aws-icon-node') || nodeGroup.querySelector('g.aws-fallback-node')) return;

            var parsed = parseNodeLabel(getNodeLabelText(nodeGroup));
            var text = parsed.clean;
            var isBottleneck = parsed.isBottleneck;

            var bbox;
            try {
                bbox = nodeGroup.getBBox();
            } catch (e) {
                return;
            }
            if (!bbox || !(bbox.width > 0)) return;

            hideNodeShapes(nodeGroup);

            var iconPath = window.matchAwsIcon(text);
            var layer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            layer.setAttribute('class', 'aws-icon-node aws-node-interactive' + (isBottleneck ? ' aws-icon-node-bottleneck' : ''));

            if (iconPath) {
                var scaled = isHorizontallyScaledNode(nodeGroup, text);
                var layout = scaled
                    ? layoutScaledIconNode(bbox, isBottleneck)
                    : layoutIconNode(bbox, ICON_SIZE, isBottleneck);
                layout.labelWidth = measureLabelWidth(text);
                layer.classList.add(scaled ? 'aws-icon-node-scaled' : 'aws-icon-node-aws');
                layer.appendChild(createAwsLabel(layout.cx, layout.labelTop, text, layout.labelWidth, layout.labelHeight));
                appendIconGraphics(layer, layout.cx, layout.bodyTopY, iconPath, scaled);
                if (isBottleneck) {
                    var badgeY = scaled ? layout.bodyTopY + layout.boxH : layout.bodyTopY;
                    var badgeSize = scaled ? SCALE_ICON_SIZE : ICON_SIZE;
                    layer.appendChild(createBottleneckBadge(layout.cx, badgeY, badgeSize));
                }
            } else {
                var shape = resolveNodeShape(nodeGroup, text);
                var scaled = isHorizontallyScaledNode(nodeGroup, text);
                if (scaled) {
                    var scaledLayout = layoutScaledIconNode(bbox, isBottleneck);
                    scaledLayout.labelWidth = measureLabelWidth(text);
                    layer.classList.add('aws-icon-node-scaled');
                    layer.appendChild(createAwsLabel(scaledLayout.cx, scaledLayout.labelTop, text, scaledLayout.labelWidth, scaledLayout.labelHeight));
                    layer.appendChild(createScaledFallbackNode(scaledLayout.cx, scaledLayout.bodyTopY, text, shape, isBottleneck));
                } else {
                    var cx = bbox.x + bbox.width / 2;
                    var cy = bbox.y + bbox.height / 2;
                    layer.appendChild(createFallbackNode(cx, cy, text, shape, isBottleneck));
                }
            }

            nodeGroup.appendChild(layer);
            nodeGroup.classList.add('aws-icon-node-processed');
        });
    };

    function roundSvgRect(rect, rx) {
        if (!rect) return;
        rect.setAttribute('rx', String(rx));
        rect.setAttribute('ry', String(rx));
    }

    function hideArchitectureClusters(svgEl) {
        if (!svgEl) return;
        svgEl.querySelectorAll('g.cluster').forEach(function(cluster) {
            var rect = cluster.querySelector(':scope > rect');
            if (rect) {
                rect.setAttribute('fill', 'none');
                rect.setAttribute('stroke', 'none');
                rect.style.opacity = '0';
                rect.style.pointerEvents = 'none';
            }
            cluster.querySelectorAll('.cluster-label, .aws-cluster-title-wrap').forEach(function(el) {
                el.style.opacity = '0';
                el.style.pointerEvents = 'none';
            });
        });
    }

    window.hideArchitectureClusters = hideArchitectureClusters;
    window.prepareArchitectureClusters = hideArchitectureClusters;

    function getEdgeLabelText(edgeLabel) {
        var textEl = edgeLabel.querySelector('foreignObject div')
            || edgeLabel.querySelector('.label span')
            || edgeLabel.querySelector('.label')
            || edgeLabel.querySelector('span')
            || edgeLabel.querySelector('text');
        return textEl ? String(textEl.textContent || '').trim() : '';
    }

    function polishEdgeLabels(svgEl) {
        if (!svgEl) return;

        var fontSize = 13;
        var padH = 14;
        var padV = 9;

        svgEl.querySelectorAll('g.edgeLabel').forEach(function(edgeLabel) {
            edgeLabel.style.overflow = 'visible';
            edgeLabel.classList.add('aws-edge-label-interactive');

            var text = getEdgeLabelText(edgeLabel);
            var rect = edgeLabel.querySelector('rect');
            if (!rect) return;

            var labelW = Math.min(240, Math.max(56, (text.length || 4) * 7.8 + padH * 2));
            var labelH = fontSize + padV * 2 + 4;

            var rx = parseFloat(rect.getAttribute('x') || '0');
            var ry = parseFloat(rect.getAttribute('y') || '0');
            var rw = parseFloat(rect.getAttribute('width') || '0');
            var rh = parseFloat(rect.getAttribute('height') || '0');
            var cx = rx + rw / 2;
            var cy = ry + rh / 2;

            rect.setAttribute('x', String(cx - labelW / 2));
            rect.setAttribute('y', String(cy - labelH / 2));
            rect.setAttribute('width', String(labelW));
            rect.setAttribute('height', String(labelH));
            rect.style.fill = 'rgba(255, 255, 255, 0.94)';
            rect.style.stroke = '#e2e8f0';
            rect.style.strokeWidth = '1px';
            roundSvgRect(rect, 10);

            var fo = edgeLabel.querySelector('foreignObject');
            if (fo) {
                fo.setAttribute('x', String(cx - labelW / 2));
                fo.setAttribute('y', String(cy - labelH / 2));
                fo.setAttribute('width', String(labelW));
                fo.setAttribute('height', String(labelH));
                fo.style.overflow = 'visible';
            }

            edgeLabel.querySelectorAll('.label, span, p, foreignObject div, text').forEach(function(el) {
                el.style.color = '#5f6d7e';
                el.style.fontSize = fontSize + 'px';
                el.style.fontStyle = 'italic';
                el.style.fontWeight = '400';
                el.style.fontFamily = 'Georgia, "Iowan Old Style", "Palatino Linotype", Palatino, serif';
                el.style.lineHeight = '1.4';
                el.style.letterSpacing = '0.02em';
                el.style.textAlign = 'center';
                el.style.whiteSpace = 'nowrap';
                el.style.overflow = 'visible';
            });
        });
    }

    function isAsyncEdgePath(path) {
        if (!path) return false;
        var dash = path.getAttribute('stroke-dasharray') || path.style.strokeDasharray || '';
        if (dash && dash !== '0' && dash !== 'none' && dash.indexOf(',') !== -1) return true;
        var edge = path.closest('g.edgePath, g.flowchart-link');
        if (edge && (edge.classList.contains('dotted') || edge.classList.contains('dashed'))) return true;
        return false;
    }

    window.styleAwsArchitectureSvg = function(svgEl) {
        if (!svgEl) return;

        svgEl.classList.add('aws-architecture-svg');
        svgEl.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

        svgEl.querySelectorAll('g.edgePath, g.flowchart-link').forEach(function(edgeGroup) {
            edgeGroup.classList.add('aws-edge-interactive');
            var path = edgeGroup.querySelector('path.path, path');
            if (!path) return;
            path.classList.add('aws-edge-path');
            var asyncEdge = isAsyncEdgePath(path);
            path.style.strokeLinecap = 'round';
            path.style.strokeLinejoin = 'round';
            path.style.fill = 'none';
            path.style.strokeWidth = '2.5px';
            if (asyncEdge) {
                path.style.stroke = '#7c5cdb';
                path.style.strokeDasharray = '9 6';
                edgeGroup.classList.add('aws-edge-async');
            } else {
                path.style.stroke = '#3d7a5a';
                path.style.strokeDasharray = 'none';
                edgeGroup.classList.add('aws-edge-sync');
            }
            var arrow = edgeGroup.querySelector('.arrowheadPath');
            if (arrow) {
                arrow.classList.add('aws-edge-arrowhead');
                arrow.style.stroke = asyncEdge ? '#7c5cdb' : '#3d7a5a';
                arrow.style.fill = asyncEdge ? '#7c5cdb' : '#3d7a5a';
            }
        });

        polishEdgeLabels(svgEl);
        hideArchitectureClusters(svgEl);
    };

    function getDiagramZoom(wrap) {
        return (wrap && wrap._diagramZoom) ? wrap._diagramZoom : { k: 1, x: 0, y: 0 };
    }

    function diagramTransformCss(wrap) {
        var zoom = getDiagramZoom(wrap);
        if (zoom.k === 1 && zoom.x === 0 && zoom.y === 0) return '';
        return 'translate(' + zoom.x + 'px, ' + zoom.y + 'px) scale(' + zoom.k + ')';
    }

    function getDiagramStage(wrap) {
        return wrap ? wrap.querySelector('.aws-diagram-stage') : null;
    }

    function clientToAnnotationCoords(wrap, clientX, clientY) {
        var stage = getDiagramStage(wrap);
        var layer = wrap.querySelector('.aws-annotation-layer');
        if (!stage || !layer) {
            var rect = wrap.getBoundingClientRect();
            return {
                x: clientX - rect.left + wrap.scrollLeft,
                y: clientY - rect.top + wrap.scrollTop
            };
        }

        window.syncArchitectureAnnotationLayer(wrap, diagramTransformCss(wrap));

        var rect = stage.getBoundingClientRect();
        var baseW = stage.offsetWidth || rect.width || 1;
        var scale = rect.width / baseW;
        if (!isFinite(scale) || scale <= 0) scale = 1;

        var pivotX = rect.left + rect.width / 2;
        var pivotY = rect.top;
        var x = (clientX - pivotX) / scale + baseW / 2;
        var y = (clientY - pivotY) / scale;

        if (!isFinite(x) || !isFinite(y)) {
            var wrapRect = wrap.getBoundingClientRect();
            return {
                x: clientX - wrapRect.left + wrap.scrollLeft,
                y: clientY - wrapRect.top + wrap.scrollTop
            };
        }

        return { x: x, y: y };
    }

    window.syncArchitectureAnnotationLayer = function(wrap, transform) {
        if (!wrap) return;
        var stage = getDiagramStage(wrap);
        var svg = wrap.querySelector('svg');
        var layer = wrap.querySelector('.aws-annotation-layer');
        if (!svg || !layer) return;

        layer.style.left = '0px';
        layer.style.top = '0px';
        layer.style.width = svg.offsetWidth + 'px';
        layer.style.height = svg.offsetHeight + 'px';
        layer.style.transform = '';
        layer.style.transformOrigin = '';
        svg.style.transform = '';
        svg.style.transformOrigin = '';

        var target = stage || wrap;
        if (transform) {
            target.style.transformOrigin = 'top center';
            target.style.transform = transform;
        } else {
            target.style.transform = '';
            target.style.transformOrigin = '';
        }
    };

    function selectAnnotationNote(wrap, note, options) {
        options = options || {};
        var prev = wrap._selectedAnnotationNote;
        if (prev) prev.classList.remove('aws-annotation-selected');
        wrap._selectedAnnotationNote = note || null;
        if (note) {
            note.classList.add('aws-annotation-selected');
            if (!options.skipWrapFocus) {
                if (!wrap.hasAttribute('tabindex')) {
                    wrap.setAttribute('tabindex', '-1');
                }
                wrap.focus({ preventScroll: true });
            }
        }
    }

    function deleteAnnotationNote(wrap, layer, note) {
        if (!note) return;
        if (wrap._selectedAnnotationNote === note) {
            wrap._selectedAnnotationNote = null;
        }
        note.remove();
        saveAnnotations(wrap.dataset.annotationDiagramId, layer);
    }

    function finalizeActiveAnnotation(wrap, layer) {
        if (!layer) return;
        var active = document.activeElement;
        if (!active || !active.classList || !active.classList.contains('aws-annotation-input')) return;
        if (!layer.contains(active)) return;
        var note = active.closest('.aws-annotation-note');
        if (!note) return;
        finishAnnotationEditing(wrap, layer, note, active);
    }

    function finishAnnotationEditing(wrap, layer, note, textarea) {
        var value = (textarea.value || '').trim();
        if (!value) {
            deleteAnnotationNote(wrap, layer, note);
            return;
        }
        textarea.value = value;
        autoGrowAnnotationInput(textarea, note);
        saveAnnotations(wrap.dataset.annotationDiagramId, layer);
        if (document.activeElement === textarea) {
            textarea.blur();
        }
    }

    function measureAnnotationTextWidth(textarea) {
        var style = window.getComputedStyle(textarea);
        var lines = (textarea.value || textarea.placeholder || ' ').split('\n');
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        if (ctx && style.font) {
            ctx.font = style.font;
        }
        var maxW = 120;
        lines.forEach(function(line) {
            var w = ctx ? ctx.measureText(line || ' ').width : line.length * 7.5;
            if (w > maxW) maxW = w;
        });
        return Math.min(560, Math.max(120, Math.ceil(maxW) + 24));
    }

    function autoGrowAnnotationInput(textarea, note) {
        if (!textarea || !note) return;
        textarea.style.overflow = 'hidden';

        if (note.dataset.userSized === '1') {
            var boxH = parseFloat(note.style.height) || note.offsetHeight || 44;
            textarea.style.height = Math.max(44, boxH) + 'px';
            return;
        }

        var targetW = measureAnnotationTextWidth(textarea);
        note.style.width = targetW + 'px';
        note.style.height = '';

        textarea.style.height = '0';
        var scrollH = textarea.scrollHeight;
        textarea.style.height = Math.max(44, scrollH) + 'px';
    }

    function bindAnnotationResize(wrap, layer, note, textarea) {
        var handle = note.querySelector('.aws-annotation-resize-handle');
        if (!handle) return;

        handle.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();

            var startX = e.clientX;
            var startY = e.clientY;
            var startW = note.offsetWidth;
            var startH = note.offsetHeight;
            var zoomK = getDiagramZoom(wrap).k;

            note.dataset.userSized = '1';
            selectAnnotationNote(wrap, note);

            function onMove(ev) {
                var newW = Math.max(120, startW + (ev.clientX - startX) / zoomK);
                var newH = Math.max(44, startH + (ev.clientY - startY) / zoomK);
                note.style.width = newW + 'px';
                note.style.height = newH + 'px';
                textarea.style.height = Math.max(44, newH) + 'px';
            }

            function onUp() {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                saveAnnotations(wrap.dataset.annotationDiagramId, layer);
            }

            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    }

    function bindAnnotationDrag(wrap, layer, note, textarea) {
        note.addEventListener('mousedown', function(e) {
            if (e.button !== 0) return;
            if (e.target.closest('.aws-annotation-resize-handle')) return;
            if (e.target.closest('.aws-annotation-input') && document.activeElement === textarea) return;

            e.preventDefault();
            e.stopPropagation();

            if (document.activeElement === textarea && e.target !== textarea) {
                textarea.blur();
            }

            var startX = e.clientX;
            var startY = e.clientY;
            var origLeft = parseFloat(note.style.left) || 0;
            var origTop = parseFloat(note.style.top) || 0;
            var zoomK = getDiagramZoom(wrap).k;
            var moved = false;

            note.classList.add('aws-annotation-dragging');
            selectAnnotationNote(wrap, note);

            function onMove(ev) {
                var dx = (ev.clientX - startX) / zoomK;
                var dy = (ev.clientY - startY) / zoomK;
                if (!moved && Math.abs(dx) < 3 && Math.abs(dy) < 3) return;
                moved = true;
                note._didDrag = true;
                note.style.left = (origLeft + dx) + 'px';
                note.style.top = (origTop + dy) + 'px';
            }

            function onUp() {
                note.classList.remove('aws-annotation-dragging');
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                if (moved) {
                    saveAnnotations(wrap.dataset.annotationDiagramId, layer);
                } else {
                    note._didDrag = false;
                }
            }

            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    }

    function applyAnnotationSize(note, item) {
        if (!note || !item) return;
        if (item.width) note.style.width = item.width + 'px';
        if (item.height) note.style.height = item.height + 'px';
        if (item.userSized) note.dataset.userSized = '1';
    }

    function createAnnotationNote(wrap, layer, x, y, text, id, startEditing, sizeMeta) {
        var note = document.createElement('div');
        note.className = 'aws-annotation-note';
        note.dataset.id = id || ('ann-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7));
        note.style.left = x + 'px';
        note.style.top = y + 'px';

        var textarea = document.createElement('textarea');
        textarea.className = 'aws-annotation-input';
        textarea.rows = 1;
        textarea.placeholder = 'Add a note…';
        textarea.value = text || '';
        textarea.setAttribute('spellcheck', 'true');
        textarea.setAttribute('wrap', 'soft');

        var resizeHandle = document.createElement('div');
        resizeHandle.className = 'aws-annotation-resize-handle';
        resizeHandle.setAttribute('aria-hidden', 'true');

        note.appendChild(textarea);
        note.appendChild(resizeHandle);
        layer.appendChild(note);

        applyAnnotationSize(note, sizeMeta);

        textarea.addEventListener('mousedown', function(e) {
            if (document.activeElement === textarea) {
                e.stopPropagation();
            }
        });
        textarea.addEventListener('click', function(e) {
            e.stopPropagation();
            selectAnnotationNote(wrap, note);
        });

        textarea.addEventListener('input', function() {
            autoGrowAnnotationInput(textarea, note);
        });

        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                finishAnnotationEditing(wrap, layer, note, textarea);
                return;
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                if (!(textarea.value || '').trim()) {
                    deleteAnnotationNote(wrap, layer, note);
                } else {
                    textarea.blur();
                }
            }
        });

        textarea.addEventListener('blur', function() {
            if (note.dataset.creating === '1') return;
            var value = (textarea.value || '').trim();
            if (!value) {
                deleteAnnotationNote(wrap, layer, note);
            } else {
                textarea.value = value;
                autoGrowAnnotationInput(textarea, note);
                saveAnnotations(wrap.dataset.annotationDiagramId, layer);
            }
        });

        note.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            if (!e.target.closest('.aws-annotation-input') && !e.target.closest('.aws-annotation-resize-handle')) {
                finalizeActiveAnnotation(wrap, layer);
            }
        });

        note.addEventListener('click', function(e) {
            e.stopPropagation();
            if (note._didDrag) {
                note._didDrag = false;
                return;
            }
            selectAnnotationNote(wrap, note);
            if (e.target.closest('.aws-annotation-input') && document.activeElement !== textarea) {
                setTimeout(function() { textarea.focus(); }, 0);
            }
        });

        note.addEventListener('dblclick', function(e) {
            e.stopPropagation();
            selectAnnotationNote(wrap, note);
            setTimeout(function() { textarea.focus(); }, 0);
        });

        bindAnnotationDrag(wrap, layer, note, textarea);
        bindAnnotationResize(wrap, layer, note, textarea);
        autoGrowAnnotationInput(textarea, note);

        if (startEditing !== false && !text) {
            note.dataset.creating = '1';
            selectAnnotationNote(wrap, note, { skipWrapFocus: true });
            autoGrowAnnotationInput(textarea, note);
            textarea.focus({ preventScroll: true });
            setTimeout(function() {
                delete note.dataset.creating;
            }, 300);
        }

        return note;
    }

    function saveAnnotations(diagramId, layer) {
        if (!diagramId || !layer) return;
        var items = [];
        layer.querySelectorAll('.aws-annotation-note').forEach(function(note) {
            var ta = note.querySelector('textarea');
            var text = ta ? ta.value.trim() : '';
            if (!text) return;
            var item = {
                id: note.dataset.id,
                x: parseFloat(note.style.left) || 0,
                y: parseFloat(note.style.top) || 0,
                text: text
            };
            var w = parseFloat(note.style.width);
            var h = parseFloat(note.style.height);
            if (w > 0) item.width = w;
            if (h > 0) item.height = h;
            if (note.dataset.userSized === '1') item.userSized = true;
            items.push(item);
        });
        annotationStore[diagramId] = items;
        persistAnnotationsToServer(diagramId, items);
    }

    function persistAnnotationsToServer(diagramId, items, immediate) {
        if (!diagramId || diagramId === 'draft' || diagramId === 'null' || diagramId === 'undefined') return;
        clearTimeout(annotationPersistTimers[diagramId]);
        var payload = JSON.stringify({ annotations: items || [] });
        var url = '/api/aws-architecture-diagrams/' + encodeURIComponent(diagramId) + '/annotations';
        if (immediate) {
            fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: payload,
                keepalive: true
            }).catch(function(err) {
                console.warn('Failed to save architecture annotations:', err);
            });
            return;
        }
        annotationPersistTimers[diagramId] = setTimeout(function() {
            fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: payload
            }).catch(function(err) {
                console.warn('Failed to save architecture annotations:', err);
            });
        }, 500);
    }

    window.addEventListener('beforeunload', function() {
        Object.keys(annotationStore).forEach(function(diagramId) {
            persistAnnotationsToServer(diagramId, annotationStore[diagramId], true);
        });
    });

    function restoreAnnotations(diagramId, wrap, layer) {
        layer.innerHTML = '';
        var items = annotationStore[diagramId] || [];
        items.forEach(function(item) {
            createAnnotationNote(wrap, layer, item.x, item.y, item.text, item.id, false, {
                width: item.width,
                height: item.height,
                userSized: item.userSized
            });
        });
    }

    window.attachArchitectureAnnotations = function(wrap, diagramId, initialAnnotations) {
        if (!wrap) return;

        var mount = getDiagramStage(wrap) || wrap;
        var layer = wrap.querySelector('.aws-annotation-layer');
        if (!layer) {
            layer = document.createElement('div');
            layer.className = 'aws-annotation-layer';
            mount.appendChild(layer);
        }

        var diagramKey = String(diagramId || 'draft');
        if (initialAnnotations != null && diagramId) {
            annotationStore[diagramKey] = initialAnnotations;
        }

        if (wrap.dataset.annotationDiagramId !== diagramKey) {
            if (wrap.dataset.annotationDiagramId) {
                saveAnnotations(wrap.dataset.annotationDiagramId, layer);
            }
            wrap.dataset.annotationDiagramId = diagramKey;
            restoreAnnotations(diagramKey, wrap, layer);
        }

        window.syncArchitectureAnnotationLayer(wrap, diagramTransformCss(wrap));

        if (wrap.dataset.annotationsBound === '1') return;
        wrap.dataset.annotationsBound = '1';

        wrap.addEventListener('dblclick', function(e) {
            if (e.target.closest('.aws-annotation-note')) return;

            e.preventDefault();
            e.stopPropagation();

            var coords = clientToAnnotationCoords(wrap, e.clientX, e.clientY);
            createAnnotationNote(wrap, layer, coords.x - 8, coords.y - 12, '', null, true);
        }, true);

        function onPointerDownFinalize(e) {
            if (!wrap.isConnected) {
                document.removeEventListener('mousedown', onPointerDownFinalize, true);
                return;
            }
            if (e.detail > 1) return;
            if (e.target.closest('.aws-annotation-input')) return;
            if (e.target.closest('.aws-annotation-note')) return;
            finalizeActiveAnnotation(wrap, layer);
        }
        document.addEventListener('mousedown', onPointerDownFinalize, true);

        wrap.addEventListener('click', function(e) {
            if (!e.target.closest('.aws-annotation-note')) {
                selectAnnotationNote(wrap, null);
            }
        });

        wrap.addEventListener('keydown', function(e) {
            var selected = wrap._selectedAnnotationNote;
            if (!selected || !wrap.contains(selected)) return;
            if (e.key !== 'Delete' && e.key !== 'Backspace') return;

            var active = document.activeElement;
            var ta = selected.querySelector('.aws-annotation-input');
            if (active === ta) return;

            e.preventDefault();
            deleteAnnotationNote(wrap, layer, selected);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { window.loadAwsIconManifest(); });
    } else {
        window.loadAwsIconManifest();
    }
})();
