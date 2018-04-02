// Cxx Test file

/** Function Foo Documentation
 * @param x A X coordinate
 * @param y A Y coordinate
 * @param z - unused
 * @returns Wether x + y are greater 0.
 *
 * This is a test comment.
 * Autolink symbols:
 * malloc() free()
 * EIO ::EIO #EIO #EINTR
 * pthread_attr_init pthread_attr_init() ::pthread_attr_init #pthread_attr_init
 * pthread_attr_t ::pthread_attr_t #pthread_attr_t pthread_attr_t()
 */
bool
foo (int x, double y, float z)
{
  // Ignore z...
  return x + y > 0;
}

/// One more function, bar()
/// @param unreal Orphan parameter
/// @returns Nothing, void.
/// Reference a previously documented function: foo()
void	bar()	{}
