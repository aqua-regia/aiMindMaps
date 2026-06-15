"""Index and search AWS architecture icons from aws_icons/png-512."""
import os
import re
from typing import List, Dict, Optional, Tuple

# Project root (aiMindMap/)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS_ROOT = os.path.join(_ROOT, 'aws_icons', 'png-512')

# Common abbreviations / diagram labels → icon filename (without .png)
ALIASES: Dict[str, str] = {
    'sqs': 'Simple-Queue-Service',
    'sns': 'Simple-Notification-Service',
    'api gateway': 'API-Gateway',
    'apigateway': 'API-Gateway',
    'alb': 'Elastic-Load-Balancing',
    'nlb': 'Elastic-Load-Balancing',
    'elb': 'Elastic-Load-Balancing',
    'load balancer': 'Elastic-Load-Balancing',
    'load balancing': 'Elastic-Load-Balancing',
    'ecs': 'Elastic-Container-Service',
    'eks': 'Elastic-Kubernetes-Service',
    'ecr': 'Elastic-Container-Registry',
    'fargate': 'Fargate',
    'lambda': 'Lambda',
    'ec2': 'EC2',
    'rds': 'RDS',
    'aurora': 'Aurora',
    'dynamodb': 'DynamoDB',
    'dynamo db': 'DynamoDB',
    'db': 'DynamoDB',
    'database': 'RDS',
    'data store': 'DynamoDB',
    'datastore': 'DynamoDB',
    'postgres': 'RDS',
    'postgresql': 'RDS',
    'mysql': 'RDS',
    'sql': 'RDS',
    'nosql': 'DynamoDB',
    'kafka': 'Managed-Streaming-for-Apache-Kafka',
    'msk': 'Managed-Streaming-for-Apache-Kafka',
    'rabbitmq': 'MQ',
    'grpc': 'API-Gateway',
    'websocket': 'API-Gateway',
    'x-ray': 'X-Ray',
    'xray': 'X-Ray',
    'tracing': 'X-Ray',
    'observability': 'CloudWatch',
    's3': 'Simple-Storage-Service',
    'bucket': 'Simple-Storage-Service',
    'elasticache': 'ElastiCache',
    'redis': 'ElastiCache',
    'memcached': 'ElastiCache',
    'cache': 'ElastiCache',
    'cloudfront': 'CloudFront',
    'cdn': 'CloudFront',
    'route 53': 'Route-53',
    'route53': 'Route-53',
    'dns': 'Route-53',
    'cognito': 'Cognito',
    'cloudwatch': 'CloudWatch',
    'vpc': 'Virtual-Private-Cloud',
    'private link': 'PrivateLink',
    'privatelink': 'PrivateLink',
    'api': 'API-Gateway',
    'appsync': 'AppSync',
    'eventbridge': 'EventBridge',
    'step functions': 'Step-Functions',
    'stepfunctions': 'Step-Functions',
    'kinesis': 'Kinesis',
    'glue': 'Glue',
    'athena': 'Athena',
    'redshift': 'Redshift',
    'emr': 'EMR',
    'sagemaker': 'SageMaker',
    'bedrock': 'Bedrock',
    'amplify': 'Amplify',
    'beanstalk': 'Elastic-Beanstalk',
    'documentdb': 'DocumentDB',
    'neptune': 'Neptune',
    'timestream': 'Timestream',
    'opensearch': 'OpenSearch-Service',
    'elasticsearch': 'OpenSearch-Service',
    'secrets manager': 'Secrets-Manager',
    'kms': 'Key-Management-Service',
    'iam': 'Identity-and-Access-Management',
    'waf': 'WAF',
    'shield': 'Shield',
    'guardduty': 'GuardDuty',
    'mobile client': 'Amplify',
    'web client': 'Amplify',
    'client': 'Amplify',
    'browser': 'Amplify',
    'mobile app': 'Amplify',
    'user': 'Amplify',
    'users': 'Amplify',
    'post service': 'Lambda',
    'microservice': 'Lambda',
    'microservices': 'Elastic-Container-Service',
    'ecs services': 'Elastic-Container-Service',
    'eks services': 'Elastic-Kubernetes-Service',
    'backend services': 'Elastic-Container-Service',
    'services': 'Elastic-Container-Service',
    'service': 'Lambda',
    'kubernetes': 'Elastic-Kubernetes-Service',
    'k8s': 'Elastic-Kubernetes-Service',
    'worker': 'Elastic-Kubernetes-Service',
    'workers': 'Elastic-Kubernetes-Service',
    'executor': 'Elastic-Kubernetes-Service',
    'mongodb': 'DocumentDB',
    'mongo': 'DocumentDB',
    'scheduler': 'EventBridge',
    'orchestrator': 'Step-Functions',
    'orchestration': 'Step-Functions',
    'agent': 'Step-Functions',
    'pipeline': 'CodePipeline',
    'deploy': 'CodeDeploy',
    'deployment': 'CodePipeline',
    'ci cd': 'CodePipeline',
    'cicd': 'CodePipeline',
    'ingress': 'Elastic-Load-Balancing',
    'metrics': 'CloudWatch',
    'logging': 'CloudWatch',
    'prometheus': 'CloudWatch',
    'experiment': 'SageMaker',
    'a b test': 'SageMaker',
    'ab test': 'SageMaker',
    'tenant': 'Cognito',
    'graph': 'Neptune',
}

_index_cache: Optional[List[Dict]] = None
_by_filename: Optional[Dict[str, Dict]] = None


def _normalize(text: str) -> str:
    text = (text or '').lower()
    text = re.sub(r'\b(amazon|aws)\b', ' ', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return ' '.join(text.split())


def _compact(text: str) -> str:
    return _normalize(text).replace(' ', '')


def _tokens_from_filename(filename: str) -> List[str]:
    base = os.path.splitext(filename)[0]
    parts = re.split(r'[-_]+', base.lower())
    tokens = set(parts)
    tokens.add(_compact(base))
    tokens.add(' '.join(parts))
    if len(parts) > 1:
        tokens.add(''.join(parts))
    return [t for t in tokens if t]


def build_index() -> List[Dict]:
    """Scan png-512 tree and build searchable icon index."""
    global _index_cache, _by_filename
    if _index_cache is not None:
        return _index_cache

    icons: List[Dict] = []
    by_filename: Dict[str, Dict] = {}

    if not os.path.isdir(ICONS_ROOT):
        _index_cache = icons
        _by_filename = by_filename
        return icons

    for dirpath, _, filenames in os.walk(ICONS_ROOT):
        for filename in sorted(filenames):
            if not filename.lower().endswith('.png'):
                continue
            full_path = os.path.join(dirpath, filename)
            rel = os.path.relpath(full_path, os.path.join(_ROOT, 'aws_icons'))
            url_path = '/aws-icons/' + rel.replace(os.sep, '/')
            base = os.path.splitext(filename)[0]
            name = base.replace('-', ' ').replace('_', ' ')
            tokens = set(_tokens_from_filename(filename))
            tokens.add(_normalize(name))
            tokens.add(_compact(name))
            entry = {
                'path': url_path,
                'file': filename,
                'name': name,
                'category': os.path.basename(dirpath),
                'tokens': sorted(tokens),
            }
            icons.append(entry)
            by_filename[base.lower()] = entry
            by_filename[_compact(base)] = entry

    _index_cache = icons
    _by_filename = by_filename
    return icons


def _score_label_against_icon(label_norm: str, label_compact: str, icon: Dict) -> int:
    score = 0
    name_norm = _normalize(icon['name'])
    name_compact = _compact(icon['name'])

    if label_compact and name_compact and label_compact == name_compact:
        return 1000
    if label_norm and name_norm and label_norm == name_norm:
        return 950
    if name_compact and name_compact in label_compact:
        score = max(score, 800 + len(name_compact))
    if name_norm and name_norm in label_norm:
        score = max(score, 700 + len(name_norm))

    for token in icon['tokens']:
        t_norm = _normalize(token)
        t_compact = _compact(token)
        if len(t_compact) < 2:
            continue
        if t_compact == label_compact:
            score = max(score, 900)
        elif t_compact in label_compact:
            score = max(score, 500 + len(t_compact))
        elif t_norm in label_norm:
            score = max(score, 400 + len(t_norm))

    label_words = set(label_norm.split())
    name_words = set(name_norm.split())
    overlap = label_words & name_words
    if overlap:
        score = max(score, 300 + 50 * len(overlap))

    return score


def match_icon(label: str) -> Optional[Dict]:
    """Find the best matching icon for a diagram node label."""
    if not label or not str(label).strip():
        return None

    build_index()
    if not _index_cache:
        return None

    label_norm = _normalize(label)
    label_compact = _compact(label)
    if not label_norm:
        return None

    # Exact alias for short labels (e.g. "db", "s3")
    if _by_filename and label_compact in ALIASES:
        target = ALIASES[label_compact]
        key = target.lower()
        if key in _by_filename:
            return _by_filename[key]
        compact_key = _compact(target)
        if compact_key in _by_filename:
            return _by_filename[compact_key]

    # Explicit alias lookup (longest match first)
    best_alias = None
    best_alias_len = 0
    for alias, filename in ALIASES.items():
        alias_norm = _normalize(alias)
        if alias_norm in label_norm and len(alias_norm) > best_alias_len:
            best_alias = filename
            best_alias_len = len(alias_norm)
    if best_alias and _by_filename:
        key = best_alias.lower()
        if key in _by_filename:
            return _by_filename[key]
        compact_key = _compact(best_alias)
        if compact_key in _by_filename:
            return _by_filename[compact_key]

    best: Optional[Dict] = None
    best_score = 0
    for icon in _index_cache:
        score = _score_label_against_icon(label_norm, label_compact, icon)
        if score > best_score:
            best_score = score
            best = icon

    return best if best_score >= 300 else None


def get_manifest() -> Dict:
    """Return icon manifest for client-side matching."""
    icons = build_index()
    return {
        'count': len(icons),
        'icons': icons,
        'aliases': ALIASES,
    }
