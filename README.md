# Cloudify - Vultr Cloud Plugin
A Cloudify Plugin that provisions resources in Vultr cloud | https://www.vultr.com

## Vultr Weirdness
### Can't delete servers before 5 minutes
Vultr requires servers to have been instantiated for at least 5 minutes before they can be requested to be terminated.  This is their requirement, not ours. We simply give output indicating that Cloudify is waiting until Vultr will allow us to request the removal.

### The Cloudify "Simple Manager Blueprint" results in a broken Manager
This is due to the way Vultr "assigns" private IP addresses to instances.  Basically, they don't. :) 
You'll need to follow the steps outlined in https://www.vultr.com/docs/configuring-private-network to manually add the reserved private IP in your Vultr dashboard to your actual server before you'll be able to actually use your manager (as it relies on having a working private IP).
