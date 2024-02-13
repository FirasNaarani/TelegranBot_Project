try {
    // reconfig the replica members, to remove the last member [setup]
    config = rs.conf();
    config.members.pop();
    rs.reconfig(config, {force: true});
} catch (error) {
    throw new Error('Failed to reconfigure: ' + error.message);
}