//[*]-------------------------------------------------------------------------[*]
//
//  GPIO IRQ Test Application.
//
//[*]-------------------------------------------------------------------------[*]
// run with sudo ./gpio_irq <pin#> 
// Connect gpio from gps to odroid shifter shield.  This program checks for pps signal as interrupt 
// and print it to console.  
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <sched.h>

//[*]-------------------------------------------------------------------------[*]
#define SYSFS_GPIO_DIR  "/sys/class/gpio"
#define POLL_TIMEOUT    (3 * 1000) /* 3 seconds */
#define MAX_BUF         64

//[*]-------------------------------------------------------------------------[*]
int gpio_export(unsigned int gpio)
{
	int fd, len;
	char buf[MAX_BUF];
 
	fd = open(SYSFS_GPIO_DIR "/export", O_WRONLY);
	if (fd < 0) {
		perror("gpio/export");
		return fd;
	}
 
	len = snprintf(buf, sizeof(buf), "%d", gpio);
	write(fd, buf, len);
	close(fd);
 
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_unexport(unsigned int gpio)
{
	int fd, len;
	char buf[MAX_BUF];
 
	fd = open(SYSFS_GPIO_DIR "/unexport", O_WRONLY);
	if (fd < 0) {
		perror("gpio/export");
		return fd;
	}
 
	len = snprintf(buf, sizeof(buf), "%d", gpio);
	write(fd, buf, len);
	close(fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_set_dir(unsigned int gpio, unsigned int out_flag)
{
	int fd, len;
	char buf[MAX_BUF];
 
	len = snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR  "/gpio%d/direction", gpio);
 
	fd = open(buf, O_WRONLY);
	if (fd < 0) {
		perror("gpio/direction");
		return fd;
	}
 
	if (out_flag)
		write(fd, "out", 4);
	else
		write(fd, "in", 3);
	close(fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_set_value(unsigned int gpio, unsigned int value)
{
	int fd, len;
	char buf[MAX_BUF];
 
	len = snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
 
	fd = open(buf, O_WRONLY);
	if (fd < 0) {
		perror("gpio/set-value");
		return fd;
	}
 
	if (value)
		write(fd, "1", 2);
	else
		write(fd, "0", 2);
 
	close(fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_get_value(unsigned int gpio, unsigned int *value)
{
	int fd, len;
	char buf[MAX_BUF];
	char ch;

	len = snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
 
	fd = open(buf, O_RDONLY);
	if (fd < 0) {
		perror("gpio/get-value");
		return fd;
	}
 
	read(fd, &ch, 1);

	if (ch != '0') {
		*value = 1;
	} else {
		*value = 0;
	}
 
	close(fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_set_edge(unsigned int gpio, char *edge)
{
	int fd, len;
	char buf[MAX_BUF];

	len = snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/edge", gpio);
 
	fd = open(buf, O_WRONLY);
	if (fd < 0) {
		perror("gpio/set-edge");
		return fd;
	}
 
	write(fd, edge, strlen(edge) + 1); 
	close(fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_fd_open(unsigned int gpio)
{
	int fd, len;
	char buf[MAX_BUF];

	len = snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
 
	fd = open(buf, O_RDONLY | O_NONBLOCK );
	if (fd < 0) {
		perror("gpio/fd_open");
	}
	return fd;
}

//[*]-------------------------------------------------------------------------[*]
int gpio_fd_close(int fd)
{
	return close(fd);
}

//[*]-------------------------------------------------------------------------[*]

int main(int argc, char **argv, char **envp)
{

	//pollfd is a struct with 3 members: int fd(descriptor), short events(specified events), short revents(events found returned).
	//fdset is a list of pollfd structs
	struct pollfd fdset[2]; // this creates an array of pollfd structs called fdset
	int nfds = 2; //the number of items in fdset
	int gpio_fd, timeout, rc;
	char *buf[MAX_BUF];	
	unsigned int gpio; //the gpio pin number to read in
	int len;

	if (argc < 2) {
		printf("Usage: aml_gpio_irq <gpio_pin>\n\n");
		printf("Waits for a change in the GPIO pin voltage level or input on stdin\n");
		exit(-1);
	}
	
	gpio = atoi(argv[1]);

	gpio_export(gpio);
	gpio_set_dir(gpio, 0);
	gpio_set_edge(gpio, "both");    // High/Low Edge Trigger
	gpio_fd = gpio_fd_open(gpio);

	timeout = POLL_TIMEOUT;

    // set a high priority schedulling for the running program
    {
        struct sched_param sched ;
        
        memset (&sched, 0, sizeof(sched)) ;
        
        sched.sched_priority = 55;
        
        sched_setscheduler (0, SCHED_RR, &sched) ;
    }

	//while (1) {
	for(int z = 0; z <= 100; z++){
		memset((void*)fdset, 0, sizeof(fdset)); //set initial values of fdset to 0?
		//pollfd is a struct with 3 members: int fd(descriptor), short events(specified events), short revents(events found returned).
		//fdset is a list of pollfd structs
		fdset[0].fd = STDIN_FILENO;
		fdset[0].events = POLLIN; //POLLIN is urgent data
      
		fdset[1].fd = gpio_fd;
		fdset[1].events = POLLPRI; //POLLPRI is normal data
		
		//poll will take a list of pollfd, number of items in pollfd list, and timeout duration
		rc = poll(fdset, nfds, timeout);      

		if (rc < 0) {
			printf("\npoll() failed!\n");
			return -1;
		}
      
		if (rc == 0) {
			printf("POLL Timeout!\n");
		}
            
		if (fdset[1].revents & POLLPRI) {
			len = read(fdset[1].fd, buf, MAX_BUF);
			printf("\npoll() GPIO %d interrupt occurred # %d\n", gpio, z);
		}

		if (fdset[0].revents & POLLIN) {
			(void)read(fdset[0].fd, buf, 1);
			printf("\npoll() stdin read 0x%2.2X\n", (unsigned int) buf[0]);
		}

		fflush(stdout);
	}
	gpio_unexport(gpio);
	gpio_fd_close(gpio_fd);
	return 0;
}

//[*]-------------------------------------------------------------------------[*]
//[*]-------------------------------------------------------------------------[*]
