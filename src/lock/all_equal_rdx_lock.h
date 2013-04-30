#include <stdbool.h>
#include "multi_writers_queue.h"
#include "common_lock_constants.h"

#ifndef ALL_EQUAL_RDX_LOCK_H
#define ALL_EQUAL_RDX_LOCK_H

struct NodeImpl;

typedef union CacheLinePaddedNodePtrImpl {
    struct NodeImpl * value;
    char padding[64];
} CacheLinePaddedNodePtr;


typedef struct NodeImpl {
    MWQueue writeQueue;
    CacheLinePaddedNodePtr next;
    CacheLinePaddedBool locked;
    CacheLinePaddedBool readSpinningEnabled;
    CacheLinePaddedInt readSpinnerFlags[NUMBER_OF_READER_GROUPS];
    bool readLockIsWriteLock;
    bool readLockIsSpinningOnNode;
    struct NodeImpl * readLockSpinningNode;
    char pad[64 - ((sizeof(bool)*2 + sizeof(struct NodeImpl *)) % 64)];
} Node;

typedef struct AllEqualRDXLockImpl {
    char pad1[64];
    void (*writer)(void *);
    char pad2[64 - sizeof(void (*)(void*)) % 64];
    CacheLinePaddedNodePtr endOfQueue;
    CacheLinePaddedInt readLocks[NUMBER_OF_READER_GROUPS];
} AllEqualRDXLock;



AllEqualRDXLock * aerlock_create(void (*writer)(void *));
void aerlock_free(AllEqualRDXLock * lock);
void aerlock_initialize(AllEqualRDXLock * lock, void (*writer)(void *));
void aerlock_register_this_thread();
void aerlock_write(AllEqualRDXLock *lock, void * writeInfo);
void aerlock_write_read_lock(AllEqualRDXLock *lock);
void aerlock_write_read_unlock(AllEqualRDXLock * lock);
void aerlock_read_lock(AllEqualRDXLock *lock);
void aerlock_read_unlock(AllEqualRDXLock *lock);

#endif
