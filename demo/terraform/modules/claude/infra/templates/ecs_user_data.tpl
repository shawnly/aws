#!/bin/bash
rm -f /etc/ecs/ecs.config
echo ECS_CLUSTER=${project}-${environment}-ecs-${event_id} >> /etc/ecs/ecs.config
# Additional setup commands can be added here