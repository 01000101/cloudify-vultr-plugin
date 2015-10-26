# Cloudify - Vultr Cloud Plugin
A Cloudify Plugin that provisions resources in Vultr cloud | https://www.vultr.com

**This project is no longer maintained**

***Vultr is an inviable cloud provider for any cloud orchestration or automation (as of 10/26/2015, see issues below)***

## Vultr Weirdness
### Can't delete servers before 5 minutes
Vultr requires servers to have been instantiated for at least 5 minutes before they can be requested to be terminated.  This is their requirement, not ours. We simply give output indicating that Cloudify is waiting until Vultr will allow us to request the removal.

### The Cloudify "Simple Manager Blueprint" results in a broken Manager
This is due to the way Vultr "assigns" private IP addresses to instances.  Basically, they don't. :) 
You'll need to follow the steps outlined in https://www.vultr.com/docs/configuring-private-network to manually add the reserved private IP in your Vultr dashboard to your actual server before you'll be able to actually use your manager (as it relies on having a working private IP).

### No outbound NAT on the private network
There is no external Internet access from an assigned private IP (network).  This is a significant problem as, because of this, it requires that the Cloudify manager act as a router to the public Internet for all private hosts (ones without public IPs still assigned to them).  This means that, effectively, all hosts deployed in Vultr must either have a public IP assigned (and in use), or that it routes all outbound traffic through another Vultr host with a public IP assigned and routing available to the public Internet.  After speaking with Vultr support, this is an approach they're sticking with for the long-term, thus making Vultr an inviable solution for most (all?) cloud orchestration.  
