import yaml
from typing import Optional, List, Tuple

from models import ProvisionerConfig, EC2NodeClassConfig

# Canonical Graviton prefixes – both instance families and full types
GRAVITON_PREFIXES = [
    "m6g", "c6g", "r6g", "m7g", "c7g", "r7g",
    "t4g", "x2gd", "im4gn", "is4gen", "g5g",
    "c6gn", "c6gd", "r6gd", "m6gd",
]


# =====================================================================
# Top-level parser
# =====================================================================


def parse_provisioner_yaml(
    yaml_content: str,
) -> Tuple[List[ProvisionerConfig], List[EC2NodeClassConfig]]:
    """
    Parse a YAML string that may contain:
      - kind: Provisioner
      - kind: NodePool
      - kind: EC2NodeClass

    Returns:
      (provisioners_and_nodepools, ec2_nodeclasses)
    """
    provisioners: List[ProvisionerConfig] = []
    nodeclasses: List[EC2NodeClassConfig] = []

    try:
        documents = list(yaml.safe_load_all(yaml_content))
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {str(e)}")

    for doc in documents:
        if not isinstance(doc, dict):
            # Ignore empty docs, comments-only docs, etc.
            continue

        kind = doc.get("kind", "")
        if kind in ("Provisioner", "NodePool"):
            provisioners.append(extract_provisioner_config(doc))
        elif kind == "EC2NodeClass":
            nodeclasses.append(extract_nodeclass_config(doc))

    return provisioners, nodeclasses


# =====================================================================
# EC2NodeClass extraction
# =====================================================================


def extract_nodeclass_config(doc: dict) -> EC2NodeClassConfig:
    metadata = doc.get("metadata", {}) or {}
    name = metadata.get("name", "unnamed-ec2nodeclass")

    spec = doc.get("spec", {}) or {}

    instance_types = [str(t) for t in (spec.get("instanceTypes") or [])]

    ami_selector_present = bool(
        spec.get("amiSelectorTerms")
        or spec.get("amiSelector")
        or spec.get("amiFamily")
        or spec.get("amiSelectorIDs")
        or spec.get("amiSelectorTags")
    )

    security_groups_present = bool(
        spec.get("securityGroupSelectorTerms")
        or spec.get("securityGroupSelector")
        or spec.get("securityGroups")
    )

    subnets_present = bool(
        spec.get("subnetSelectorTerms")
        or spec.get("subnetSelector")
        or spec.get("subnets")
    )

    instance_profile = spec.get("instanceProfile")
    role = spec.get("role")

    return EC2NodeClassConfig(
        name=name,
        instance_types=instance_types,
        ami_selector_present=ami_selector_present,
        security_groups_present=security_groups_present,
        subnets_present=subnets_present,
        instance_profile=instance_profile,
        role=role,
        raw_yaml=doc,
    )


# =====================================================================
# Provisioner / NodePool extraction
# =====================================================================


def extract_provisioner_config(doc: dict) -> ProvisionerConfig:
    metadata = doc.get("metadata", {}) or {}
    name = metadata.get("name", "unnamed")

    kind = doc.get("kind", "Provisioner")
    spec = doc.get("spec", {}) or {}

    consolidation_enabled = extract_consolidation(spec)
    spot_allowed = extract_spot_capacity(spec, doc)
    instance_families = extract_instance_families(spec, doc)
    graviton_used = check_graviton_usage(instance_families)
    ttl_seconds = extract_ttl(spec, doc)

    nodeclass_name: Optional[str] = None
    if kind == "NodePool":
        # Typical Karpenter pattern:
        # spec.template.spec.nodeClass.name or similar
        template = spec.get("template", {}) or {}
        template_spec = template.get("spec", {}) if isinstance(template, dict) else {}
        nodeclass_ref = (
            template_spec.get("nodeClass")
            or spec.get("nodeClass")
            or spec.get("nodeClassRef")
        )

        if isinstance(nodeclass_ref, str):
            nodeclass_name = nodeclass_ref
        elif isinstance(nodeclass_ref, dict):
            # support both { name: .. } and nested nameRef
            nodeclass_name = (
                nodeclass_ref.get("name")
                or nodeclass_ref.get("nameRef")
                or (
                    isinstance(nodeclass_ref.get("nameRef"), dict)
                    and nodeclass_ref["nameRef"].get("name")
                )
            )

    return ProvisionerConfig(
        name=name,
        kind=kind,
        nodeclass_name=nodeclass_name,
        consolidation_enabled=consolidation_enabled,
        spot_allowed=spot_allowed,
        instance_families=instance_families,
        graviton_used=graviton_used,
        ttl_seconds_after_empty=ttl_seconds,
        raw_yaml=doc,
    )


# =====================================================================
# Consolidation
# =====================================================================


def extract_consolidation(spec: dict) -> Optional[bool]:
    """
    Try to determine whether consolidation is enabled, disabled or unset.

    Returns:
      True  -> explicitly enabled / aggressive disruption config
      False -> explicitly disabled
      None  -> not specified / unknown
    """
    # Karpenter v0.x Consolidation API
    consolidation = spec.get("consolidation", {})
    if isinstance(consolidation, dict) and "enabled" in consolidation:
        return bool(consolidation.get("enabled"))

    # Karpenter v1.x Disruption API (top level)
    disruption = spec.get("disruption", {})
    if isinstance(disruption, dict):
        policy = disruption.get("consolidationPolicy", "")
        if isinstance(policy, str) and policy:
            pl = policy.lower()
            if pl == "whenempty" or pl == "empty":
                return False
            if pl in ("whenunderutilized", "underutilized"):
                return True

        budgets = disruption.get("budgets", [])
        if budgets:
            # Having budgets configured usually implies consolidation is on
            return True

    # NodePool-style: spec.template.spec.disruption
    template = spec.get("template", {}) or {}
    template_spec = template.get("spec", {}) if isinstance(template, dict) else {}
    template_disruption = (
        template_spec.get("disruption", {}) if isinstance(template_spec, dict) else {}
    )
    if isinstance(template_disruption, dict):
        policy = template_disruption.get("consolidationPolicy", "")
        if isinstance(policy, str) and policy:
            pl = policy.lower()
            if pl == "whenempty" or pl == "empty":
                return False
            if pl in ("whenunderutilized", "underutilized"):
                return True

    return None


# =====================================================================
# Spot capacity
# =====================================================================


def extract_spot_capacity(spec: dict, doc: dict) -> bool:
    """
    Detect whether Spot capacity is allowed for this provisioner.
    """
    all_requirements = get_all_requirements(spec, doc)

    for req in all_requirements:
        key = str(req.get("key", ""))
        if "capacity-type" in key.lower():
            values = req.get("values", [])
            operator = str(req.get("operator", "In")).lower()

            if operator in ("in", "exists"):
                if "spot" in [str(v).lower() for v in values]:
                    return True

    # Look at labels as a fallback
    labels = get_all_labels(spec, doc)
    for key, value in labels.items():
        if "capacity-type" in str(key).lower():
            if isinstance(value, str) and value.lower() == "spot":
                return True
            if isinstance(value, list) and "spot" in [str(v).lower() for v in value]:
                return True

    # Karpenter 'constraints' block
    constraints = spec.get("constraints", {})
    if isinstance(constraints, dict):
        capacity_types = constraints.get("capacityTypes", [])
        if "spot" in [str(ct).lower() for ct in capacity_types]:
            return True

    # Legacy provider.capacityType
    provider = spec.get("provider", {})
    if isinstance(provider, dict):
        capacity_type = provider.get("capacityType", "")
        if isinstance(capacity_type, str) and capacity_type.lower() == "spot":
            return True
        if isinstance(capacity_type, list) and "spot" in [
            str(ct).lower() for ct in capacity_type
        ]:
            return True

    return False


# =====================================================================
# Instance families / Graviton
# =====================================================================


def extract_instance_families(spec: dict, doc: dict) -> List[str]:
    """
    Collect instance *families* in use, based on requirements and constraints.
    """
    families = set()
    all_requirements = get_all_requirements(spec, doc)

    for req in all_requirements:
        key = str(req.get("key", ""))
        values = req.get("values", [])

        key_lower = key.lower()
        if "instance-family" in key_lower:
            for v in values:
                if v:
                    families.add(str(v))
        elif "instance-type" in key_lower:
            for v in values:
                fam = extract_family_from_type(str(v))
                if fam:
                    families.add(fam)
        elif "instance-size" in key_lower:
            # Not enough information from size alone – skip.
            continue

    constraints = spec.get("constraints", {})
    if isinstance(constraints, dict):
        instance_types = constraints.get("instanceTypes", [])
        for it in instance_types:
            fam = extract_family_from_type(str(it))
            if fam:
                families.add(fam)

    return list(families)


def extract_family_from_type(instance_type: str) -> Optional[str]:
    if not instance_type:
        return None
    parts = instance_type.split(".")
    if not parts:
        return None
    return parts[0]


def check_graviton_usage(instance_families: List[str]) -> bool:
    """
    Return True if any of the detected instance families look like Graviton.
    """
    for family in instance_families:
        fl = family.lower()
        for prefix in GRAVITON_PREFIXES:
            if fl.startswith(prefix) or prefix in fl:
                return True
    return False


# =====================================================================
# Requirements / labels helpers
# =====================================================================


def get_all_requirements(spec: dict, doc: dict) -> List[dict]:
    """
    Gather all 'requirements' arrays we care about from different nesting
    locations used by Karpenter.
    """
    requirements: List[dict] = []

    direct_reqs = spec.get("requirements", [])
    if isinstance(direct_reqs, list):
        requirements.extend(direct_reqs)

    template = spec.get("template", {}) or {}
    template_spec = template.get("spec", {}) if isinstance(template, dict) else {}
    template_reqs = template_spec.get("requirements", [])
    if isinstance(template_reqs, list):
        requirements.extend(template_reqs)

    provider = spec.get("provider", {})
    if isinstance(provider, dict):
        provider_reqs = provider.get("requirements", [])
        if isinstance(provider_reqs, list):
            requirements.extend(provider_reqs)

    return requirements


def get_all_labels(spec: dict, doc: dict) -> dict:
    """
    Collect labels from metadata and template metadata.
    """
    labels: dict = {}

    metadata = doc.get("metadata", {}) or {}
    meta_labels = metadata.get("labels", {})
    if isinstance(meta_labels, dict):
        labels.update(meta_labels)

    template = spec.get("template", {}) or {}
    template_metadata = template.get("metadata", {}) if isinstance(template, dict) else {}
    template_labels = template_metadata.get("labels", {})
    if isinstance(template_labels, dict):
        labels.update(template_labels)

    spec_labels = spec.get("labels", {})
    if isinstance(spec_labels, dict):
        labels.update(spec_labels)

    return labels


# =====================================================================
# TTL extraction
# =====================================================================


def extract_ttl(spec: dict, doc: dict) -> Optional[int]:
    """
    Try hard to derive an effective ttlSecondsAfterEmpty for this provisioner.

    We support:
      - spec.ttlSecondsAfterEmpty
      - spec.disruption.consolidateAfter (duration string)
      - spec.disruption.expireAfter (duration string)
      - spec.template.spec.disruption.expireAfter
      - spec.template.metadata.annotations[*ttl*|*expire*]
      - spec.ttlSecondsUntilExpired (legacy)
    """
    # Direct legacy field
    ttl = spec.get("ttlSecondsAfterEmpty")
    if ttl is not None:
        try:
            return int(ttl)
        except (ValueError, TypeError):
            pass

    # Disruption API (top-level)
    disruption = spec.get("disruption", {})
    if isinstance(disruption, dict):
        consolidate_after = disruption.get("consolidateAfter")
        if consolidate_after:
            seconds = parse_duration_to_seconds(str(consolidate_after))
            if seconds is not None:
                return seconds

        expire_after = disruption.get("expireAfter")
        if expire_after:
            seconds = parse_duration_to_seconds(str(expire_after))
            if seconds is not None:
                return seconds

    # NodePool template disruption
    template = spec.get("template", {}) or {}
    template_spec = template.get("spec", {}) if isinstance(template, dict) else {}
    template_disruption = (
        template_spec.get("disruption", {}) if isinstance(template_spec, dict) else {}
    )
    if isinstance(template_disruption, dict):
        expire_after = template_disruption.get("expireAfter")
        if expire_after:
            seconds = parse_duration_to_seconds(str(expire_after))
            if seconds is not None:
                return seconds

    # Look for TTL-ish annotations on the template metadata
    template_metadata = template.get("metadata", {}) if isinstance(template, dict) else {}
    annotations = template_metadata.get("annotations", {})
    if isinstance(annotations, dict):
        for key, value in annotations.items():
            if "ttl" in str(key).lower() or "expire" in str(key).lower():
                seconds = parse_duration_to_seconds(str(value))
                if seconds is not None:
                    return seconds

    # Legacy ttlSecondsUntilExpired
    ttl_until_expired = spec.get("ttlSecondsUntilExpired")
    if ttl_until_expired is not None:
        try:
            return int(ttl_until_expired)
        except (ValueError, TypeError):
            pass

    return None


def parse_duration_to_seconds(duration: str) -> Optional[int]:
    """
    Parse simple duration strings into seconds.

    Supported forms:
      - plain integer seconds: "300"
      - Go-style-ish combos: "1h30m", "2h", "10m", "45s", "1d2h"
      - Special values: "never", "none", "inf", "infinity" -> None
    """
    if not duration:
        return None

    duration_str = str(duration).strip().lower()
    if duration_str in ("never", "none", "inf", "infinity"):
        return None

    # Already plain integer seconds
    if duration_str.isdigit():
        return int(duration_str)

    total_seconds = 0
    current_num = ""

    for char in duration_str:
        if char.isdigit():
            current_num += char
            continue

        if char in ("d", "h", "m", "s"):
            if not current_num:
                continue
            num = int(current_num)
            if char == "d":
                total_seconds += num * 86400
            elif char == "h":
                total_seconds += num * 3600
            elif char == "m":
                total_seconds += num * 60
            elif char == "s":
                total_seconds += num
            current_num = ""

    # Any trailing number without unit -> assume seconds
    if current_num:
        total_seconds += int(current_num)

    return total_seconds if total_seconds > 0 else None