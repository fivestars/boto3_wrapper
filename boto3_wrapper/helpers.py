import time
from pprint import pprint


class Helper(object):
    def __init__(self, boto_session):
        self._bs = boto_session

    ASG_STABLE = 'STABLE'
    ASG_SCALING = 'SCALING_UP'
    ASG_SUSPENDED = 'SUSPENDED_PROCESS'

    def describe_auto_scaling_state(self, AutoScalingGroupNames):
        """
        Describe an autoscaling state, returning :
        - STABLE
        - SCALING
        - SUSPENDED_PROCESS
        :return: a dict { asg_name: (state, msg) }
        """

        asg_state = self._bs.asg.describe_auto_scaling_groups(AutoScalingGroupNames=AutoScalingGroupNames)

        res = {}
        for asg in asg_state:
            res[asg['AutoScalingGroupName']] = self._get_asg_state(**asg)
        return res

    def _get_asg_state(self, Instances, DesiredCapacity, SuspendedProcesses, **kwargs):
        nb_inst = len(Instances)

        if SuspendedProcesses:
            return self.ASG_SUSPENDED, ' '.join(p['ProcessName'] for p in SuspendedProcesses)

        if nb_inst == 0 and DesiredCapacity == 0:
            return self.ASG_STABLE, 'ASG desactivated'

        i_states = set(i['LifecycleState'].split(':')[0] for i in Instances)
        i_health = set(i['HealthStatus'] for i in Instances)
        i_id = [i['InstanceId'] for i in Instances]

        if i_health != {'Healthy'}:
            return self.ASG_SCALING, 'Some instances are unhealthy'

        if {'Pending'} & i_states:
            return self.ASG_SCALING, 'Some instances are still pending'
        if {'Terminated', 'Terminating'} & i_states:
            return self.ASG_SCALING, 'Some instances are still beiing terminated'
        if {'Detaching', 'Detached', 'Quarantined', 'EnteringStandby', 'Standby'} & i_states:
            return self.ASG_SCALING, 'Some instances are detaching or in standby'

        # This is the first case, before even the asg react we have that info
        # In the case everyone is in service
        if nb_inst > DesiredCapacity:
            return self.ASG_SCALING, '%s => %s More instances than desired' % (nb_inst, DesiredCapacity)
        if nb_inst < DesiredCapacity:
            return self.ASG_SCALING, '%s => %s Less instances than desired' % (nb_inst, DesiredCapacity)

        # now test the instance check state, which may not be valid if it just started
        i_status_raw = self._bs.ec2.describe_instance_status(InstanceIds=i_id, IncludeAllInstances=True)
        for i in i_status_raw:
            st = (i['InstanceState']['Name'], i['SystemStatus']['Status'], i['InstanceStatus']['Status'])
            if st != ('running', 'ok', 'ok'):
                return self.ASG_SCALING, 'instance(s) are still starting'

        return self.ASG_STABLE, None

