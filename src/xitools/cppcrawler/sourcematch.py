from abc import ABC, abstractclassmethod


## Abstract class to represent regex.Match-like matches in SourceFile-s.
# @anchor SourceMatch
class SourceMatch(ABC):
    
    ## Constructor that has to be called in child classes.
    #
    # @param src         The SourceFile in which the match was made.
    # @param copySource  If True, a shallow copy of src is made for internal use. Set False only if src will not 
    #                    be modified. Otherwise the object can become invalid.
    def __init__(self, sourcefile, copySource=True):
        self.__sourcefile = sourcefile.copy() if copySource else sourcefile


    ## Equivalent to SourceMatch.group.
    def __getitem__(self, *groups):
        return self.group(*groups)


    ## Order based on the positions of entire matches (group 0). Comparing with None is always False.
    def __lt__(self, other):
        if other is None: 
            return False
        else:
            return (self.intStart(), self.intEnd()) < (other.intStart(), other.intEnd())


    ## The positional equality of entire matches (group 0).
    def __eq__(self, other):
        if other is None: 
            return False
        else:
            return (self.intStart(), self.intEnd()) == (other.intStart(), other.intEnd())
        

    def __str__(self):
        return (f"<xitools.cppcrawler.{type(self).__name__} object; "
                f"start={self.startLoc()}, end={self.endLoc()} match='{self.group(0)}'>")


    def __repr__(self):
        return (f"<xitools.cppcrawler.{type(self).__name__} object at {hex(id(self))}; "
                f"start={self.startLoc()}, end={self.endLoc()} match='{self.group(0)}'>")


    ## Returns the path to the source file (in the moment of the match creation).
    def filepath(self):
        return self.__sourcefile.filepath()
    

    def _intCode(self):
        return self.__sourcefile.intCode()

    
    def _group1(self, group):
        return self.__sourcefile._SourceFile__code[self.intStart(group):self.intEnd(group)]


    ## Returns one or more subgroups of the match. 
    #
    # If there is a single argument, the result is a single string; if there are multiple arguments, the result is 
    # a tuple with one item per argument. No arguments is equivalent to passing 0. The 0 argument results in the
    # entire match.
    def group(self, *groups):
        match len(groups):
            case 0: return self._group1(0)
            case 1: return self._group1(groups[0])
            case _: return tuple(self._group1(g) for g in groups)
    

    ## Returns the indices of the starts of the substrings matched by subgroups.
    #
    # If there is a single argument, the result is a single number; if there are multiple arguments, the result is 
    # a tuple with one item per argument. No arguments is equivalent to passing 0. The 0 argument means the entire 
    # match. If a passed group exists, but did not contribute to the match, -1 is returned.
    def start(self, *groups):
        match len(groups):
            case 0: return self.__sourcefile.orgPos(self.intStart(0))
            case 1: return self.__sourcefile.orgPos(self.intStart(groups[0]))
            case _: return tuple(self.__sourcefile.orgPos(self.intStart(g)) for g in groups)
    
    
    ## Returns the indices of the ends of the substrings matched by subgroups.
    #
    # If there is a single argument, the result is a single number; if there are multiple arguments, the result is 
    # a tuple with one item per argument. No arguments is equivalent to passing 0. The 0 argument means the entire 
    # match. If a passed group exists, but did not contribute to the match, -1 is returned.
    def end(self, *groups):
        match len(groups):
            case 0: return self.__sourcefile.orgPos(self.intEnd(0))
            case 1: return self.__sourcefile.orgPos(self.intEnd(groups[0]))
            case _: return tuple(self.__sourcefile.orgPos(self.intEnd(g)) for g in groups)
    

    ## Returns the location (pair: line, position in the line) of the indice returned by SourceMatch.start.
    def startLoc(self, group=0):
        return self.__sourcefile.orgLocation(self.intStart(group), int=True)
    

    ## Returns the location (pairs: line, position in the line) of the indice returned by SourceMatch.end.
    def endLoc(self, group=0):
        return self.__sourcefile.orgLocation(self.intEnd(group), int=True)
    

    ## Same as SourceMatch.start, but returns internal indices.
    @abstractclassmethod
    def intStart(self, *groups):
        pass
    
    
    ## Same as SourceMatch.end, but returns internal indices.
    @abstractclassmethod
    def intEnd(self, *groups):
        pass

        
    ## Returns a dictionary containing all the named subgroups of the match, keyed by the subgroup name.
    #
    # The default argument is used for groups that did not participate in the match; it defaults to None.
    @abstractclassmethod
    def groupdict(self, default=None):
        pass
    

    ## Returns a tuple containing all the subgroups of the match from 1.
    #
    # The default argument is used for groups that did not participate in the match; it defaults to None.
    @abstractclassmethod
    def groups(self, default=None):
        pass
    

    ## Returns all substrings that were matched to the given group.
    @abstractclassmethod
    def captures(self, group=0):
        pass
    
    
    ## Returns all start indices of substrings that were matched to the given group.
    @abstractclassmethod
    def starts(self, group=0):
        pass
    
    
    ## Returns all end indices of substrings that were matched to the given group.
    @abstractclassmethod
    def ends(self, group=0):
        pass
    


## Impementation of SourceMatch that wraps regex.Match.
#
# For the description of the methods see SourceMatch.
class SourceRegexMatch(SourceMatch):

    ##
    # @param src   The SourceFile.
    # @param mres  The regex.Match that was matched in src.
    # @param copySource  If True, a shallow copy of src is made for internal use. Set False only if src will not 
    #                    be modified. Otherwise the object can become invalid.
    def __init__(self, src, mres, *, copySource=True):
        assert mres
        SourceMatch.__init__(self, src, copySource)
        self.__mres = mres

    def groupdict(self, default=None):
        return self.__mres.groupdict(default)

    def groups(self, default=None):
        return self.__mres.groups(default)

    def captures(self, group=0):
        return self.__mres.captures(group)

    def starts(self, group=0):
        return [self._SourceMatch__sourcefile.orgPos(pos) for pos in self.__mres.starts(group)]

    def ends(self, group=0):
        return [self._SourceMatch__sourcefile.orgPos(pos) for pos in self.__mres.ends(group)]

    def intStart(self, *groups):
        return self.__mres.start(*groups)

    def intEnd(self, *groups):
        return self.__mres.end(*groups)
    

    
## Impementation of SourceMatch that is based on a list of indice ranges in a source.
#
# For the description of the methods see SourceMatch.
class SourceRangeMatch(SourceMatch):
    
    ##
    # @param src     The SourceFile.
    # @param ranges  A pair (start, end) or a non-empty list of such pairs, where start, end are indices. The pair 
    #                with an index n, defines the n-th subgroup.
    # @param int     If True, the indices are internal 
    # @param copySource  If True, a shallow copy of src is made for internal use. Set False only if src will not 
    #                    be modified. Otherwise the object can become invalid.
    def __init__(self, src, ranges, *, int=False, copySource=True):
        if isinstance(ranges, tuple):
            ranges = [ranges]
        if isinstance(ranges, list):
            self.__ranges = []
            for (start, end) in ranges:
                assert 0 <= start and start <= end
                self.__ranges.append((start, end) if int else (src.intPos(start), src.intPos(end)))
        else: # pragma: no cover
            assert False, "Incorrect type of the ranges"

        SourceMatch.__init__(self, src, copySource)


    def groupdict(self, default=None):
        return {}

    def groups(self, default=None):
        return tuple(self._group1(g) for g in range(1, len(self.__ranges)))

    def captures(self, group=0):
        return [self._group1(group)]

    def starts(self, group=0):
        return [self.start(group)]

    def ends(self, group=0):
        return [self.end(group)]

    def intStart(self, *groups):
        match len(groups):
            case 0: return self.__ranges[0][0]
            case 1: return self.__ranges[groups[0]][0]
            case _: return tuple(self.__ranges[g][0] for g in groups)

    def intEnd(self, *groups):
        match len(groups):
            case 0: return self.__ranges[0][1]
            case 1: return self.__ranges[groups[0]][1]
            case _: return tuple(self.__ranges[g][1] for g in groups)
