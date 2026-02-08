# EC2 AMI selection safeguards
Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html

Notes:
- AMI selectors should be explicit enough to avoid unintended images.
- Broad or empty selectors can drift to untested AMIs.
- Prefer owned or curated AMIs with known provenance.
- Track AMI updates as part of the cluster change process.
- Validate architecture and OS compatibility for workloads.
