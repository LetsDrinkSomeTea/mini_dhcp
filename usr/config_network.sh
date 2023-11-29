ip_bin="/sbin/ip"
br_bin="/sbin/brctl"
ns_bin="/usr/bin/nsenter"
container_id=$1
container_sid=$(echo "$container_id" | cut -c1-4)
interface_int="${container_sid}-int"
interface_ext="${container_sid}-ext"
interface_int_v6="${container_sid}-int-v6"
interface_ext_v6="${container_sid}-ext-v6"

gateway="192.168.10.120"
ipv6_gateway="fe80::74a4:edff:fe9e:2856"

cpid=$(docker inspect -f '{{.State.Pid}}' "$container_id")

# Create and configure veth pair
echo "$ip_bin link add $interface_int type veth peer name $interface_ext"
$ip_bin link add $interface_int type veth peer name $interface_ext

echo "$ip_bin link set $interface_ext master br0"
$ip_bin link set $interface_ext master br0

echo "$ip_bin link set $interface_ext up"
$ip_bin link set $interface_ext up

echo "$ip_bin link set netns $cpid dev $interface_int"
$ip_bin link set netns $cpid dev $interface_int

# IPv4 configuration
echo "$ns_bin -t $cpid -n $ip_bin addr add \"$2/32\" peer $gateway dev $interface_int"
$ns_bin -t $cpid -n $ip_bin addr add "$2/32" peer $gateway dev $interface_int

echo "$ns_bin -t $cpid -n $ip_bin link set $interface_int up"
$ns_bin -t $cpid -n $ip_bin link set $interface_int up

echo "$ns_bin -t $cpid -n $ip_bin route add default via $gateway dev $interface_int"
$ns_bin -t $cpid -n $ip_bin route add default via $gateway dev $interface_int

# IPv6 configuration
echo "$ip_bin -6 link add $interface_int_v6 type veth peer name $interface_ext_v6"
$ip_bin -6 link add $interface_int_v6 type veth peer name $interface_ext_v6

echo "$ip_bin -6 link set $interface_ext_v6 master br0"
$ip_bin -6 link set $interface_ext_v6 master br0

echo "$ip_bin -6 link set $interface_ext_v6 up"
$ip_bin -6 link set $interface_ext_v6 up

echo "$ip_bin -6 link set netns $cpid dev $interface_int_v6"
$ip_bin -6 link set netns $cpid dev $interface_int_v6

echo "$ns_bin -t $cpid -n $ip_bin -6 addr add \"$3/64\" dev $interface_int_v6"
$ns_bin -t $cpid -n $ip_bin -6 addr add "$3/64" dev $interface_int_v6

echo "$ns_bin -t $cpid -n $ip_bin -6 link set $interface_int_v6 up"
$ns_bin -t $cpid -n $ip_bin -6 link set $interface_int_v6 up

echo "$ns_bin -t $cpid -n $ip_bin -6 route add ::/0 via $ipv6_gateway dev $interface_int_v6"
$ns_bin -t $cpid -n $ip_bin -6 route add ::/0 via $ipv6_gateway dev $interface_int_v6

